const API_BASE_URL = "http://localhost:8000";

export const articleService = {
  getAllArticles: async () => {
    const response = await fetch(`${API_BASE_URL}/articles`);
    if (!response.ok) throw new Error("Failed to fetch articles");
    return response.json();
  },

  filterArticles: async ({
    keyword,
    disease_name,
    location,
    from_date,
    to_date,
    risk_level,
    limit = 50,
  } = {}) => {
    const params = new URLSearchParams();
    if (keyword) params.append("keyword", keyword);
    if (disease_name) params.append("disease_name", disease_name);
    if (location) params.append("location", location);
    if (from_date) params.append("from_date", from_date);
    if (to_date) params.append("to_date", to_date);
    if (risk_level) params.append("risk_level", risk_level);
    params.append("limit", limit);

    const response = await fetch(
      `${API_BASE_URL}/api/articles/filter?${params}`,
    );
    if (!response.ok) throw new Error("Failed to filter articles");
    return response.json();
  },
};

export const reportService = {
  downloadWeeklyReport: async () => {
    const response = await fetch(
      "http://localhost:8000/api/report/weekly/download",
    );
    if (!response.ok) {
      throw new Error("Không thể tải báo cáo từ máy chủ");
    }
    return await response.blob();
  },
};
