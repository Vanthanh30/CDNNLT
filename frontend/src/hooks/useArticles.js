import { useState, useEffect, useMemo } from "react";
import { articleService } from "../services/api";

// Helper: tính from_date string (YYYY-MM-DD) từ filter range
const getRangeDateParam = (range) => {
  if (range === "Tất Cả") return null;
  const days = range === "7 Ngày Qua" ? 7 : 30;
  const d = new Date();
  d.setDate(d.getDate() - days);
  // Format YYYY-MM-DD cho backend
  return d.toISOString().split("T")[0];
};

export const useArticles = () => {
  const [articles, setArticles] = useState([]);
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [filters, setFilters] = useState({
    range: "Tất Cả",
    disease: "Tất Cả",
    location: "Tất Cả",
    risk_level: "Tất Cả",
  });

  const [currentPage, setCurrentPage] = useState(1);
  const articlesPerPage = 5;

  // Fetch tất cả bài (không filter) — dùng cho sidebar stats & dropdowns
  const fetchAllArticles = async () => {
    setIsLoading(true);
    try {
      const data = await articleService.getAllArticles();
      setArticles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("API Error:", error);
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch với filter — gọi /api/articles/filter trên backend
  const fetchFilteredArticles = async (params) => {
    setIsLoading(true);
    try {
      const data = await articleService.filterArticles(params);
      setFilteredArticles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Filter API Error:", error);
      setFilteredArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllArticles();
  }, []);

  // Mỗi khi filter hoặc searchQuery thay đổi → gọi API filter
  useEffect(() => {
    const from_date = getRangeDateParam(filters.range);

    const params = {
      keyword: searchQuery.trim() || undefined,
      disease_name: filters.disease !== "Tất Cả" ? filters.disease : undefined,
      location: filters.location !== "Tất Cả" ? filters.location : undefined,
      risk_level: filters.risk_level !== "Tất Cả" ? filters.risk_level : undefined,
      from_date: from_date || undefined,
      limit: 200,
    };

    fetchFilteredArticles(params);
    setCurrentPage(1);
  }, [filters, searchQuery]);

  const handleSearch = (e) => {
    if (e.key === "Enter") {
      // searchQuery đã được watch bởi useEffect ở trên → tự động re-fetch
      setCurrentPage(1);
    }
  };

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({
      range: "Tất Cả",
      disease: "Tất Cả",
      location: "Tất Cả",
      risk_level: "Tất Cả",
    });
    setSearchQuery("");
  };

  // Unique options cho dropdowns — lấy từ toàn bộ articles (không filter)
  const uniqueOptions = useMemo(() => {
    if (!articles.length) return { diseases: [], locations: [], tags: [] };

    const diseases = [
      ...new Set(articles.map((a) => a.disease_name).filter(Boolean)),
    ];
    const locations = [
      ...new Set(articles.map((a) => a.location).filter(Boolean)),
    ];
    const sources = [
      ...new Set(
        articles
          .map((a) => {
            try {
              return new URL(a.url || "").hostname.replace("www.", "");
            } catch {
              return null;
            }
          })
          .filter(Boolean),
      ),
    ];

    return { diseases, locations, sources, tags: diseases };
  }, [articles]);

  const totalPages = Math.ceil(filteredArticles.length / articlesPerPage) || 1;
  const currentArticles = filteredArticles.slice(
    (currentPage - 1) * articlesPerPage,
    currentPage * articlesPerPage,
  );

  return {
    isLoading,
    searchQuery,
    setSearchQuery,
    handleSearch,
    filters,
    updateFilter,
    resetFilters,
    uniqueOptions,
    articles,
    filteredArticles,
    currentArticles,
    totalArticlesCount: filteredArticles.length,
    pagination: {
      currentPage,
      totalPages,
      paginate: setCurrentPage,
    },
  };
};