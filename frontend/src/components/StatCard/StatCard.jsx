import React from 'react';
import './StatCard.css';

const StatCard = ({ title, value, subValue, color }) => {
    return (
        <div className="stat-card panel">
            <h3 className="stat-title">{title}</h3>
            <div className="stat-value">{value}</div>
            <div className={`stat-subvalue text-${color}`}>
                {subValue}
            </div>
        </div>
    );
};

export default StatCard;