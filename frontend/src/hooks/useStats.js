import { useState, useEffect } from "react";

const API_BASE_URL = "http://localhost:8000";

export const useStats = () => {
    const [stats, setStats] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/stats`);
                const data = await res.json();
                setStats(data);
            } catch (err) {
                console.error("Stats fetch error:", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchStats();
        // Tự động refresh mỗi 5 phút
        const interval = setInterval(fetchStats, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    return { stats, isLoading };
};