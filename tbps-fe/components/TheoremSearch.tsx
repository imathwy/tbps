"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Copy,
  Download,
  ChevronDown,
  Clock,
  FileText,
  Hash,
} from "lucide-react";
import {
  ServerType,
  TheoremSearchAPI,
  TheoremResult,
  EXAMPLE_EXPRESSIONS,
  SimilarTheoremsResponse,
} from "@/lib/api";

// Form validation schema
const searchSchema = z.object({
  expression: z
    .string()
    .min(1, "Expression is required")
    .max(1000, "Expression too long (max 1000 chars)"),
  k: z.number().min(1, "Must be at least 1").max(100, "Must be at most 100"),
  node_ratio: z
    .number()
    .min(1.0, "Must be at least 1.0")
    .max(2.0, "Must be at most 2.0")
    .optional()
    .nullable(),
});

type SearchFormData = z.infer<typeof searchSchema>;

interface TheoremSearchProps {
  serverType: ServerType;
}

export function TheoremSearch({ serverType }: TheoremSearchProps) {
  const [results, setResults] = useState<SimilarTheoremsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      expression: "",
      k: 20,
      node_ratio: null,
    },
  });

  const onSubmit = async (data: SearchFormData) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const api = new TheoremSearchAPI(serverType);
      const response = await api.findSimilarTheorems({
        expression: data.expression,
        k: data.k,
        node_ratio: data.node_ratio || undefined,
      });
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const setExample = (example: (typeof EXAMPLE_EXPRESSIONS)[0]) => {
    form.setValue("expression", example.expression);
  };

  const copyResult = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportResults = (format: "json" | "csv") => {
    if (!results) return;

    if (format === "json") {
      const blob = new Blob([JSON.stringify(results, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "theorem_search_results.json";
      a.click();
    } else {
      const csv = [
        "Name,Similarity Score,Statement,Node Count",
        ...results.results.map(
          (r) =>
            `"${r.name}",${r.similarity_score},"${r.statement.replace(/"/g, '""')}",${r.node_count}`,
        ),
      ].join("\n");

      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "theorem_search_results.csv";
      a.click();
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Search for Similar Theorems
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {/* Expression Input */}
              <FormField
                control={form.control}
                name="expression"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex items-center justify-between">
                      <FormLabel>Lean Expression</FormLabel>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm">
                            Examples <ChevronDown className="w-3 h-3 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-80">
                          {EXAMPLE_EXPRESSIONS.map((example, i) => (
                            <DropdownMenuItem
                              key={i}
                              onClick={() => setExample(example)}
                              className="flex flex-col items-start p-3"
                            >
                              <div className="font-medium text-sm">
                                {example.name}
                              </div>
                              <div className="text-xs text-slate-500 mt-1 font-mono">
                                {example.expression}
                              </div>
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    <FormControl>
                      <Textarea
                        placeholder="Enter a Lean expression (e.g., ∀ (a b : Nat), a + b = b + a)"
                        className="min-h-[100px] font-mono"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Enter a Lean 4 theorem statement or expression to find
                      similar theorems.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Parameters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="k"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Number of Results (k)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseInt(e.target.value))
                          }
                        />
                      </FormControl>
                      <FormDescription>
                        How many similar theorems to return (1-100)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="node_ratio"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Node Ratio (Optional)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1.0"
                          max="2.0"
                          step="0.1"
                          placeholder="Auto-determined"
                          {...field}
                          value={field.value || ""}
                          onChange={(e) =>
                            field.onChange(
                              e.target.value
                                ? parseFloat(e.target.value)
                                : null,
                            )
                          }
                        />
                      </FormControl>
                      <FormDescription>
                        Filter ratio for search optimization (1.0-2.0)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Search Similar Theorems
                  </>
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Loading Progress */}
      {loading && (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>Processing your request...</span>
                <span className="text-slate-500">
                  This may take a few seconds
                </span>
              </div>
              <Progress value={undefined} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
              <span className="font-medium">Error:</span>
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {results && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Search Results ({results.results.length})
              </CardTitle>
              <div className="flex gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-1" />
                      Export
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={() => exportResults("json")}>
                      Export as JSON
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => exportResults("csv")}>
                      Export as CSV
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">
              <div>
                Parsed expression:{" "}
                <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">
                  {results.expression_parsed}
                </code>
              </div>
              <div className="mt-1">
                Total processed: {results.total_processed} theorems
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.results.map((result, index) => (
                <Card key={index} className="relative">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <Badge variant="secondary" className="text-xs">
                            #{index + 1}
                          </Badge>
                          <h3 className="font-mono font-medium text-sm">
                            {result.name}
                          </h3>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyResult(result.name)}
                            className="h-6 w-6 p-0"
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center gap-4 text-sm">
                            <div className="flex items-center gap-2">
                              <span className="text-slate-500">Score:</span>
                              <Badge variant="outline" className="font-mono">
                                {(result.similarity_score * 100).toFixed(1)}%
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Hash className="w-3 h-3 text-slate-500" />
                              <span className="text-slate-500">
                                {result.node_count} nodes
                              </span>
                            </div>
                          </div>

                          <Progress
                            value={result.similarity_score * 100}
                            className="h-2"
                          />

                          <details className="group">
                            <summary className="cursor-pointer text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200">
                              Show theorem statement
                            </summary>
                            <div className="mt-2 p-3 bg-slate-50 dark:bg-slate-800 rounded font-mono text-sm">
                              {result.statement}
                            </div>
                          </details>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
