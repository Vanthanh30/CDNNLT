const API_BASE_URL = "http://localhost:8000";

export const articleService = {
  getAllArticles: async () => {
    const response = await fetch(`${API_BASE_URL}/articles`);
    if (!response.ok) throw new Error("Failed to fetch articles");
    return response.json();
  },

  searchArticles: async (query) => {
    const response = await fetch(`${API_BASE_URL}/search?q=${query}`);
    if (!response.ok) throw new Error("Failed to search articles");
    return response.json();
  },
};
