import Lean
import Lean.Meta
import Lean.Elab.Term
import Lean.Elab.Command
import Lean.Data.Json
open Lean Elab Term Meta Json

/-- 自定义表达式结构 -/
inductive YourExpr where
  | bvar (deBruijnIndex : Nat)
  | fvar (fvarId : String)
  | mvar (mvarId : String)
  | sort (u : String)
  | const (declName : String) (us : List String)
  | app (fn : YourExpr) (arg : YourExpr)
  | lam (binderName : String) (binderType : YourExpr) (body : YourExpr) (binderInfo : String)
  | forallE (binderName : String) (binderType : YourExpr) (body : YourExpr) (binderInfo : String)
  | letE (declName : String) (type : YourExpr) (value : YourExpr) (body : YourExpr) (nonDep : Bool)
  | lit (literal : String)
  | mdata (data : String) (expr : YourExpr)
  | proj (typeName : String) (idx : Nat) (struct : YourExpr)
  deriving ToJson, FromJson, Repr, Inhabited

structure Frame where
  node         : Expr
  childResults : Array YourExpr
  remaining    : List Expr
  deriving Inhabited

def getChildren (e : Expr) : List Expr :=
  match e with
  | Expr.app f a               => [f, a]
  | Expr.lam _ t b _           => [t, b]
  | Expr.forallE _ t b _       => [t, b]
  | Expr.letE _ t v b _        => [t, v, b]
  | Expr.mdata _ e             => [e]
  | Expr.proj _ _ s            => [s]
  | _                          => []

def reconstruct (e : Expr) (children : List YourExpr) : YourExpr :=
  match e with
  | Expr.bvar idx              => YourExpr.bvar idx
  | Expr.fvar fvarId           => YourExpr.fvar ((repr fvarId).pretty)
  | Expr.mvar mvarId           => YourExpr.mvar ((repr mvarId).pretty)
  | Expr.sort lvl              => YourExpr.sort ((repr lvl).pretty)
  | Expr.const n us            => YourExpr.const (n.toString) (us.map (fun u => (repr u).pretty))
  | Expr.app _ _ =>
      match children with
      | [f', a'] => YourExpr.app f' a'
      | _        => panic "Unexpected children count in app"
  | Expr.lam bn _ _ bi =>
      match children with
      | [t', b'] => YourExpr.lam (bn.toString) t' b' ((repr bi).pretty)
      | _        => panic "Unexpected children count in lam"
  | Expr.forallE bn _ _ bi =>
      match children with
      | [t', b'] => YourExpr.forallE (bn.toString) t' b' ((repr bi).pretty)
      | _        => panic "Unexpected children count in forallE"
  | Expr.letE dn _ _ _ nd =>
      match children with
      | [t', v', b'] => YourExpr.letE (dn.toString) t' v' b' nd
      | _            => panic "Unexpected children count in letE"
  | Expr.lit lit              => YourExpr.lit ((repr lit).pretty)
  | Expr.mdata data _ =>
      match children with
      | [e'] => YourExpr.mdata ((repr data).pretty) e'
      | _    => panic "Unexpected children count in mdata"
  | Expr.proj tn idx _  =>
      match children with
      | [s'] => YourExpr.proj (tn.toString) idx s'
      | _    => panic "Unexpected children count in proj"

partial def exprToYourExprIter (e : Expr) (maxDepth : Nat := 1000) : MetaM YourExpr := do
  let mut stack : List Frame := []
  stack := [{ node := e, childResults := #[], remaining := getChildren e }]
  while !stack.isEmpty do
    if stack.length > maxDepth then
      throwError "Iteration depth exceeded threshold"
    let top := stack.head!
    match top.remaining with
    | child :: rest =>
        stack := { top with remaining := rest } :: stack.tail!
        stack := { node := child, childResults := #[], remaining := getChildren child } :: stack
    | [] =>
        let result := reconstruct top.node (top.childResults.toList)
        stack := stack.tail!
        if stack.isEmpty then
          return result
        else
          let parent := stack.head!
          let updatedParent := { parent with childResults := parent.childResults.push result }
          stack := updatedParent :: stack.tail!
  unreachable!

def parseStringToExpr (input : String) : TermElabM Expr := do
  let env ← getEnv
  match Lean.Parser.runParserCategory env `term input with
  | Except.ok stx => elabTerm stx none
  | Except.error err => throwError s!"parser error: {err}"

def processSingleProp (inputStr : String) : TermElabM Json := do
  let e ← parseStringToExpr inputStr
  let e := (← instantiateMVars e)
  let dbgStr := e.dbgToString
  let yourExpr ← exprToYourExprIter e 1000
  let resultJson : Json := Json.mkObj [
    ("input_str", Json.str inputStr),
    ("expr_dbg", Json.str dbgStr),
    ("your_expr", toJson yourExpr),
    ("expr_cse_json", Json.null)
  ]
  pure resultJson


syntax (name := parseAndWriteCmd) "parse_and_write " str str : command

elab_rules : command
| `(parse_and_write $inS:str $outS:str) => do
  let inPath  : String := inS.getString
  let outPath : String := outS.getString
  let inputStr ← IO.FS.readFile inPath
  let inputStr := inputStr.trim
  let json ← Lean.Elab.Command.runTermElabM (fun _ => processSingleProp inputStr)
  logInfo m!"[parse_and_write] input = {inPath}, output = {outPath}"
  IO.FS.writeFile outPath (toString json)


def runViaLeanSubprocess (inPath outPath : String) : IO Unit := do
  let tmp : System.FilePath := (System.FilePath.mk ".__parse_and_write_tmp").withExtension "lean"
  let thisModule := "Mathlib_Construction"
  let content :=
s!"import {thisModule}
set_option maxRecDepth 100000
parse_and_write \"{inPath}\" \"{outPath}\"
"
  IO.FS.writeFile tmp content

  let lake := if System.Platform.isWindows then "lake.exe" else "lake"
  let child ← IO.Process.spawn {
    cmd := lake,
    args := #["env", "lean", tmp.toString],
    stdout := .inherit, stderr := .inherit
  }
  let code ← child.wait

  try IO.FS.removeFile tmp catch _ => pure ()
  if code != 0 then
    throw <| IO.userError s!"`lake env lean` exit code {code}"

def main : IO Unit := do
  let inFile  := "input_expr.txt"
  let outFile := "expr_output.json"
  IO.println s!"[runner] generating {outFile} from {inFile}..."
  runViaLeanSubprocess inFile outFile
  IO.println s!"[runner] done: {outFile}"
