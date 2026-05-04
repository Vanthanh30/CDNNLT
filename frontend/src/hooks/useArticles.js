import { useState, useEffect, useMemo } from "react";
import { articleService } from "../services/api";

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

  const fetchArticles = async (promise) => {
    setIsLoading(true);
    try {
      const data = await promise;
      setArticles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("API Error:", error);
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles(articleService.getAllArticles());
  }, []);

  const handleSearch = (e) => {
    if (e.key === "Enter") {
      const q = searchQuery.trim();
      fetchArticles(
        q === ""
          ? articleService.getAllArticles()
          : articleService.filterArticles({ keyword: q })
      );
    }
  };

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({ range: "Tất Cả", disease: "Tất Cả", location: "Tất Cả", risk_level: "Tất Cả" });
  };

  // Unique options cho dropdowns — dùng field thật từ backend
  const uniqueOptions = useMemo(() => {
    if (!articles.length) return { diseases: [], locations: [], tags: [] };

    const diseases = [...new Set(articles.map((a) => a.disease_name).filter(Boolean))];
    const locations = [...new Set(articles.map((a) => a.location).filter(Boolean))];
    const sources = [...new Set(articles.map((a) => {
      try { return new URL(a.url || "").hostname.replace("www.", ""); }
      catch { return null; }
    }).filter(Boolean))];

    return { diseases, locations, sources, tags: diseases };
  }, [articles]);

  // Apply local filters
  useEffect(() => {
    let result = articles;
    const now = new Date();

    if (filters.range === "7 Ngày Qua") {
      const limit = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      result = result.filter(
        (a) => a.processed_at && new Date(a.processed_at) >= limit
      );
    } else if (filters.range === "30 Ngày Qua") {
      const limit = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      result = result.filter(
        (a) => a.processed_at && new Date(a.processed_at) >= limit
      );
    }

    if (filters.disease !== "Tất Cả") {
      result = result.filter((a) => a.disease_name === filters.disease);
    }

    if (filters.location !== "Tất Cả") {
      result = result.filter((a) => a.location === filters.location);
    }

    if (filters.risk_level !== "Tất Cả") {
      result = result.filter((a) => a.risk_level === filters.risk_level);
    }

    setFilteredArticles(result);
    setCurrentPage(1);
  }, [articles, filters]);

  const totalPages = Math.ceil(filteredArticles.length / articlesPerPage) || 1;
  const currentArticles = filteredArticles.slice(
    (currentPage - 1) * articlesPerPage,
    currentPage * articlesPerPage
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
    currentArticles,
    totalArticlesCount: filteredArticles.length,
    pagination: {
      currentPage,
      totalPages,
      paginate: setCurrentPage,
    },
  };
};