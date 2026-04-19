import { useState, useEffect, useMemo } from "react";
import { articleService } from "../services/api";

export const useArticles = () => {
  const [articles, setArticles] = useState([]);
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [filters, setFilters] = useState({
    range: "Tất Cả",
    source: "Tất Cả",
    tag: "Tất Cả",
    location: "Tất Cả",
  });

  const [currentPage, setCurrentPage] = useState(1);
  const articlesPerPage = 5;

  // Fetch initial data
  const fetchArticles = async (fetchPromise) => {
    setIsLoading(true);
    try {
      const data = await fetchPromise;
      setArticles(data);
    } catch (error) {
      console.error("API Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles(articleService.getAllArticles());
  }, []);

  const handleSearch = (e) => {
    if (e.key === "Enter") {
      const promise =
        searchQuery.trim() === ""
          ? articleService.getAllArticles()
          : articleService.searchArticles(searchQuery);
      fetchArticles(promise);
    }
  };

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({
      range: "Tất Cả",
      source: "Tất Cả",
      tag: "Tất Cả",
      location: "Tất Cả",
    });
  };

  // Extract unique options for dropdowns
  const uniqueOptions = useMemo(() => {
    if (!articles.length) return { sources: [], tags: [] };

    const sources = articles.map((art) => {
      try {
        return new URL(art.link).hostname.replace("www.", "");
      } catch {
        return "Khác";
      }
    });

    const tags = articles.map((art) =>
      art.keywords ? art.keywords.split(",")[0].trim().toUpperCase() : "",
    );

    return {
      sources: [...new Set(sources)].filter(Boolean),
      tags: [...new Set(tags)].filter(Boolean),
    };
  }, [articles]);

  // Apply filters
  useEffect(() => {
    let result = articles;
    const now = new Date();

    if (filters.range === "7 Ngày Qua") {
      const limit = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      result = result.filter((art) => new Date(art.created_at) >= limit);
    } else if (filters.range === "30 Ngày Qua") {
      const limit = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      result = result.filter((art) => new Date(art.created_at) >= limit);
    }

    if (filters.source !== "Tất Cả") {
      result = result.filter(
        (art) => art.link && art.link.includes(filters.source),
      );
    }

    if (filters.tag !== "Tất Cả") {
      result = result.filter(
        (art) =>
          art.keywords && art.keywords.toUpperCase().includes(filters.tag),
      );
    }

    setFilteredArticles(result);
    setCurrentPage(1);
  }, [articles, filters]);

  // Pagination calculations
  const indexOfLastArticle = currentPage * articlesPerPage;
  const indexOfFirstArticle = indexOfLastArticle - articlesPerPage;
  const currentArticles = filteredArticles.slice(
    indexOfFirstArticle,
    indexOfLastArticle,
  );
  const totalPages = Math.ceil(filteredArticles.length / articlesPerPage) || 1;

  return {
    isLoading,
    searchQuery,
    setSearchQuery,
    handleSearch,
    filters,
    updateFilter,
    resetFilters,
    uniqueOptions,
    currentArticles,
    totalArticlesCount: filteredArticles.length,
    pagination: {
      currentPage,
      totalPages,
      paginate: setCurrentPage,
    },
  };
};
