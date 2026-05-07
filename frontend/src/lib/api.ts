const API_BASE_URL = "http://localhost:8000/api";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "API request failed";
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    return response.json();
  } catch (err: any) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  auth: {
    login: (data: any) => fetchApi("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    register: (data: any) => fetchApi("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    chat: (data: any) => fetchApi("/auth/chat", { method: "POST", body: JSON.stringify(data) }),
  },
  goals: {
    getCatalog: () => fetchApi("/goals/catalog"),
    getUserGoals: (userKey: string) => fetchApi(`/goals/${userKey}`),
    save: (data: any) => fetchApi("/goals/save", { method: "POST", body: JSON.stringify(data) }),
  },
  portfolio: {
    get: (userKey: string) => fetchApi(`/portfolio/${userKey}`),
    upload: (data: any) => fetchApi("/portfolio/upload", { method: "POST", body: JSON.stringify(data) }),
    review: (userKey: string) => fetchApi(`/portfolio/review/${userKey}`),
    getQuickAdvice: (data: any) => fetchApi("/portfolio/quick-advice", { method: "POST", body: JSON.stringify(data) }),
  },
  market: {
    getPriceSeries: (symbol: string, days: number = 180) => fetchApi(`/market/price/${symbol}?days=${days}`),
  }
};
