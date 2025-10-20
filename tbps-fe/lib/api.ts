// API client for Theorem Similarity Search
export interface TheoremResult {
  name: string;
  similarity_score: number;
  statement: string;
  node_count: number;
}

export interface SimilarTheoremsRequest {
  expression: string;
  k?: number;
  node_ratio?: number;
}

export interface SimilarTheoremsResponse {
  success: boolean;
  results: TheoremResult[];
  total_processed: number;
  expression_parsed: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  database_connected: boolean;
  lean_available: boolean;
}

export type ServerType = "mock" | "production";

export const API_URLS = {
  mock: "http://localhost:8001",
  production: "http://localhost:8000",
} as const;

export class TheoremSearchAPI {
  private baseUrl: string;

  constructor(serverType: ServerType = "mock") {
    this.baseUrl = API_URLS[serverType];
  }

  setServer(serverType: ServerType) {
    this.baseUrl = API_URLS[serverType];
  }

  async findSimilarTheorems(
    request: SimilarTheoremsRequest,
  ): Promise<SimilarTheoremsResponse> {
    const response = await fetch(`${this.baseUrl}/find-similar-theorems`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  async getMockInfo(): Promise<any> {
    if (this.baseUrl !== API_URLS.mock) {
      throw new Error("Mock info only available for mock server");
    }

    const response = await fetch(`${this.baseUrl}/mock-info`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  getServerInfo() {
    return {
      baseUrl: this.baseUrl,
      serverType:
        this.baseUrl === API_URLS.mock ? "mock" : ("production" as ServerType),
    };
  }
}

// Default API instance
export const apiClient = new TheoremSearchAPI();

// Example expressions for testing
export const EXAMPLE_EXPRESSIONS = [
  {
    name: "Commutative Addition (Nat)",
    expression: "∀ (a b : Nat), a + b = b + a",
  },
  {
    name: "Commutative Multiplication (Nat)",
    expression: "∀ (a b : Nat), a * b = b * a",
  },
  {
    name: "Associative Addition (Nat)",
    expression: "∀ (a b c : Nat), (a + b) + c = a + (b + c)",
  },
  {
    name: "List Length Append",
    expression:
      "∀ (α : Type) (l₁ l₂ : List α), List.length (l₁ ++ l₂) = List.length l₁ + List.length l₂",
  },
  {
    name: "Set Union Commutativity",
    expression: "∀ (α : Type) (A B : Set α), A ∪ B = B ∪ A",
  },
  {
    name: "Function Composition Associativity",
    expression: "∀ (f g h : α → β → γ), (f ∘ g) ∘ h = f ∘ (g ∘ h)",
  },
  {
    name: "Real Number Addition Commutativity",
    expression: "∀ (x y : ℝ), x + y = y + x",
  },
  {
    name: "Group Multiplication Associativity",
    expression: "∀ (G : Type) [Group G] (a b c : G), (a * b) * c = a * (b * c)",
  },
  {
    name: "List Reverse Involutive",
    expression: "∀ (α : Type) (l : List α), List.reverse (List.reverse l) = l",
  },
  {
    name: "Set Intersection Commutativity",
    expression: "∀ (α : Type) (A B : Set α), A ∩ B = B ∩ A",
  },
];
