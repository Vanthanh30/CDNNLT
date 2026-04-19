import React, { useState } from "react";
import {
  Search,
  Filter,
  ArrowUp,
  Zap,
  Play,
  Video,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { useArticles } from "../../hooks/useArticles";
import ArticleCard from "../../components/ArticleCard/ArticleCard";
import "./SearchContent.css";

const SearchContent = () => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const {
    isLoading,
    searchQuery,
    setSearchQuery,
    handleSearch,
    filters,
    updateFilter,
    resetFilters,
    uniqueOptions,
    currentArticles,
    totalArticlesCount,
    pagination,
  } = useArticles();

  return (
    <div className="search-tab-container">
      <div className="search-header">
        <h2>Công cụ Tìm kiếm Thông minh</h2>
        <p>Tổng hợp thông tin y tế và dịch bệnh từ các nguồn báo chí điện tử</p>
      </div>

      {/* Top Controls */}
      <div className="search-controls">
        <div className="search-input-box">
          <Search className="icon-search" size={20} />
          <input
            type="text"
            placeholder="Nhập từ khóa mầm bệnh (vd: covid) và ấn Enter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>

        <div className="date-filters">
          {["Tất Cả", "7 Ngày Qua", "30 Ngày Qua"].map((range) => (
            <button
              key={range}
              className={`filter-btn ${filters.range === range ? "active" : ""}`}
              onClick={() => updateFilter("range", range)}
            >
              {range}
            </button>
          ))}
        </div>

        <button
          className={`advanced-btn ${showAdvanced ? "active-adv" : ""}`}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          <Filter size={18} /> BỘ LỌC NÂNG CAO
        </button>
      </div>

      {/* Advanced Filters Panel */}
      {showAdvanced && (
        <div className="advanced-filters-panel">
          <div className="filter-group">
            <label>Nguồn Báo</label>
            <select
              value={filters.source}
              onChange={(e) => updateFilter("source", e.target.value)}
            >
              <option value="Tất Cả">Tất Cả Nguồn</option>
              {uniqueOptions.sources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Thẻ Nhãn (Tag)</label>
            <select
              value={filters.tag}
              onChange={(e) => updateFilter("tag", e.target.value)}
            >
              <option value="Tất Cả">Tất Cả Thẻ</option>
              {uniqueOptions.tags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Địa Điểm</label>
            <select
              value={filters.location}
              onChange={(e) => updateFilter("location", e.target.value)}
            >
              <option value="Tất Cả">Toàn quốc</option>
              <option value="Hà Nội">Hà Nội</option>
              <option value="Đà Nẵng">Đà Nẵng</option>
            </select>
          </div>

          <button className="clear-filter-btn" onClick={resetFilters}>
            <X size={16} /> Xóa Lọc
          </button>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="search-grid">
        <div className="main-column">
          {isLoading ? (
            <p
              style={{ textAlign: "center", padding: "40px", color: "#0ea5e9" }}
            >
              ⏳ Đang tổng hợp dữ liệu từ hệ thống Crawler...
            </p>
          ) : currentArticles.length === 0 ? (
            <p
              style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}
            >
              Không có dữ liệu phù hợp với thời gian hoặc bộ lọc này.
            </p>
          ) : (
            <>
              {currentArticles.map((art) => (
                <ArticleCard key={art.id} article={art} />
              ))}

              {pagination.totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="page-btn"
                    onClick={() =>
                      pagination.paginate(pagination.currentPage - 1)
                    }
                    disabled={pagination.currentPage === 1}
                  >
                    <ChevronLeft size={18} /> Trước
                  </button>
                  <span className="page-info">
                    Trang{" "}
                    <strong style={{ color: "#0ea5e9" }}>
                      {pagination.currentPage}
                    </strong>{" "}
                    / {pagination.totalPages}
                  </span>
                  <button
                    className="page-btn"
                    onClick={() =>
                      pagination.paginate(pagination.currentPage + 1)
                    }
                    disabled={pagination.currentPage === pagination.totalPages}
                  >
                    Sau <ChevronRight size={18} />
                  </button>
                </div>
              )}
            </>
          )}

          {/* Video Mock */}
          <div className="card video-card">
            <div className="card-header-small">
              <Video size={16} /> BẢN TIN TỔNG HỢP VIDEO
            </div>
            <div className="video-player-mock">
              <button className="play-button">
                <Play fill="currentColor" size={24} />
              </button>
              <span className="duration">12:45</span>
            </div>
          </div>
        </div>

        {/* Right Sidebar Widgets */}
        <div className="side-column">
          <div className="card widget-card">
            <div className="widget-header">
              <h3>Tóm tắt Nhanh</h3>
            </div>
            <div className="summary-list">
              <div className="summary-item">
                <div className="stat up">
                  <ArrowUp size={16} />
                  <span>Total</span>
                </div>
                <div className="stat-text">
                  <strong>TỔNG SỐ BÀI BÁO</strong>
                  <p>Hiển thị {totalArticlesCount} tin tức</p>
                </div>
              </div>
              <div className="summary-item">
                <div className="stat danger-up">
                  <ArrowUp size={16} />
                  <span>14%</span>
                </div>
                <div className="stat-text">
                  <strong>SỐT XUẤT HUYẾT</strong>
                  <p>Gia tăng đột biến ở các tỉnh miền Trung</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card alert-card">
            <div className="alert-header">
              <Zap size={18} fill="currentColor" /> CẢNH BÁO DỊCH BỆNH
            </div>
            <p>
              Phân tích tin tức cho thấy cụm lây nhiễm cúm A bất thường tại khu
              vực Quận Hải Châu. Đề xuất kiểm tra chéo ngay lập tức.
            </p>
            <button className="audit-btn">KÍCH HOẠT QUY TRÌNH KIỂM TRA</button>
          </div>

          <div className="card widget-card sentiment-card">
            <h3>Biểu đồ Mức độ Lo ngại</h3>
            <div className="bar-chart-mock">
              <div className="bar" style={{ height: "40%" }}></div>
              <div className="bar" style={{ height: "60%" }}></div>
              <div className="bar highlight" style={{ height: "90%" }}></div>
              <div className="bar" style={{ height: "50%" }}></div>
            </div>
            <p className="chart-footer">ĐỘ TIN CẬY NLP: 98.4%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchContent;
