import { useState, useEffect, useCallback } from "react";

const BASE_URL = import.meta.env.VITE_FORECAST_API_URL || "http://localhost:8010";

export const useForecast = ({ location = null, historyDays = 180, topN = 3 } = {}) => {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedDisease, setSelectedDisease] = useState(null);
    const [detailForecast, setDetailForecast] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    const fetchSummary = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({ history_days: historyDays, top_n: topN });
            if (location) params.append("location", location);
            const res = await fetch(`${BASE_URL}/forecast/diseases?${params}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setSummary(data);
            if (data.diseases?.length > 0 && !selectedDisease) {
                setSelectedDisease(data.diseases[0].disease_name);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [location, historyDays, topN]);

    const fetchDetail = useCallback(async (diseaseName) => {
        if (!diseaseName) return;
        setDetailLoading(true);
        try {
            const params = new URLSearchParams({ disease_name: diseaseName, history_days: historyDays, days: 14 });
            if (location) params.append("location", location);
            const res = await fetch(`${BASE_URL}/forecast?${params}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setDetailForecast(data);
        } catch (err) {
            console.error("Detail forecast error:", err);
        } finally {
            setDetailLoading(false);
        }
    }, [location, historyDays]);

    useEffect(() => { fetchSummary(); }, [fetchSummary]);
    useEffect(() => { if (selectedDisease) fetchDetail(selectedDisease); }, [selectedDisease, fetchDetail]);

    return {
        summary,
        loading,
        error,
        selectedDisease,
        setSelectedDisease,
        detailForecast,
        detailLoading,
        refetch: fetchSummary,
    };
};