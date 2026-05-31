import { useEffect, useState } from "react";

const API_ENDPOINTS = {
  health: "/api/health",
  search: "/api/search",
  recommend: "/api/recommend",
  details: "/api/details"
};

const QUICK_SEARCHES = ["cough syrup", "stomach pain relief", "allergy tablet"];
const QUICK_MEDS = ["Azithral 500 Tablet", "Augmentin 625 Duo Tablet", "Paracetamol", "Cetirizine"];

const parseResponseBody = async (response) => {
  const raw = await response.text();

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
};

const parseApiError = (data, fallbackMessage) => {
  if (!data) {
    return fallbackMessage;
  }

  if (typeof data === "string") {
    return data;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data.detail)) {
    const messages = data.detail
      .map((entry) => (entry && typeof entry === "object" ? entry.msg : ""))
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallbackMessage;
};

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <p>{value || "N/A"}</p>
    </div>
  );
}

function SkeletonCard() {
  return (
    <article className="result-card skeleton-card" aria-hidden="true">
      <div className="skeleton-body">
        <div className="skeleton-line skeleton-line--title" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line skeleton-line--wide" />
      </div>
    </article>
  );
}

function ResultCard({ item }) {
  return (
    <article className="result-card">
      <div className="result-card-top">
        <div className="result-heading-wrap">
          <h3>{item.name || "Unnamed medicine"}</h3>
        </div>
      </div>

      <div className="result-card-body">
        <div className="info-grid">
          <InfoRow label="Composition" value={item.composition} />
          <InfoRow label="Uses" value={item.uses} />
          <InfoRow label="Side effects" value={item.side_effects} />
        </div>

        {item.explanation ? <p className="result-copy">{item.explanation}</p> : null}

        {item.safety_note ? (
          <div className="safety-box">
            <span>Safety note</span>
            <p>{item.safety_note}</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function SectionHeader({ eyebrow, title, description }) {
  return (
    <div className="section-header">
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function EmptyState({ title, description }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

export function App() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState("");
  const [searchTouched, setSearchTouched] = useState(false);

  const [medicineName, setMedicineName] = useState("");
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");
  const [detailsResult, setDetailsResult] = useState(null);
  const [detailsTouched, setDetailsTouched] = useState(false);

  const [recommendName, setRecommendName] = useState("");
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [recommendError, setRecommendError] = useState("");
  const [recommendResults, setRecommendResults] = useState([]);
  const [recommendTouched, setRecommendTouched] = useState(false);

  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");
  const [healthLoading, setHealthLoading] = useState(true);

  const canSearch = query.trim().length > 0 && !searchLoading;
  const canDetails = medicineName.trim().length > 0 && !detailsLoading;
  const canRecommend = recommendName.trim().length > 0 && !recommendLoading;

  const updateTopK = (delta) => {
    setTopK((currentValue) => Math.max(1, currentValue + delta));
  };

  const refreshHealth = async () => {
    setHealthLoading(true);
    setHealthError("");

    try {
      const response = await fetch(API_ENDPOINTS.health);
      const data = await parseResponseBody(response);

      if (!response.ok) {
        throw new Error(parseApiError(data, "Unable to load health status."));
      }

      setHealth(data);
    } catch (error) {
      setHealthError(error instanceof Error ? error.message : "Unable to load health status.");
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    void refreshHealth();
  }, []);

  const onSearch = async (event) => {
    event.preventDefault();

    if (!canSearch) {
      return;
    }

    setSearchTouched(true);
    setSearchLoading(true);
    setSearchError("");

    try {
      const response = await fetch(API_ENDPOINTS.search, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          top_k: topK
        })
      });

      const data = await parseResponseBody(response);
      if (!response.ok) {
        throw new Error(parseApiError(data, "Search request failed."));
      }

      setSearchResults(Array.isArray(data?.results) ? data.results : []);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Search request failed.");
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const onDetails = async (event) => {
    event.preventDefault();

    if (!canDetails) {
      return;
    }

    setDetailsTouched(true);
    setDetailsLoading(true);
    setDetailsError("");

    try {
      const response = await fetch(API_ENDPOINTS.details, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ medicine_name: medicineName.trim() })
      });

      const data = await parseResponseBody(response);
      if (!response.ok) {
        throw new Error(parseApiError(data, "Unable to fetch medicine details."));
      }

      setDetailsResult(data);
    } catch (error) {
      setDetailsError(error instanceof Error ? error.message : "Unable to fetch medicine details.");
      setDetailsResult(null);
    } finally {
      setDetailsLoading(false);
    }
  };

  const onRecommend = async (event) => {
    event.preventDefault();

    if (!canRecommend) {
      return;
    }

    setRecommendTouched(true);
    setRecommendLoading(true);
    setRecommendError("");

    try {
      const response = await fetch(API_ENDPOINTS.recommend, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ medicine_name: recommendName.trim(), top_k: topK })
      });

      const data = await parseResponseBody(response);
      if (!response.ok) {
        throw new Error(parseApiError(data, "Unable to fetch recommendations."));
      }

      setRecommendResults(Array.isArray(data?.results) ? data.results : []);
    } catch (error) {
      setRecommendError(error instanceof Error ? error.message : "Unable to fetch recommendations.");
      setRecommendResults([]);
    } finally {
      setRecommendLoading(false);
    }
  };

  const indexedRecords = health && typeof health.indexed_records === "number" ? health.indexed_records.toLocaleString() : "—";
  const backendLabel = healthLoading ? "Checking" : healthError ? "Offline" : "Ready";

  return (
    <div className="app-shell">
      <div className="orb orb-a" />
      <div className="orb orb-b" />
      <div className="orb orb-c" />

      <header className="hero-panel panel">
        <div className="hero-copy">
          <p className="eyebrow">Drug intelligence dashboard</p>
          <h1>Search medicines semantically, compare alternatives, and inspect details from one polished React workspace.</h1>
          <p className="hero-description">
            Built for fast retrieval, this interface keeps the active API visible while giving search, recommendation, and detail lookup
            flows a cleaner, more deliberate presentation.
          </p>

          <div className="hero-actions">
            <button className="primary-button" type="button" onClick={refreshHealth}>
              {healthLoading ? "Refreshing health..." : "Refresh health"}
            </button>
            <div className="hero-status">
              <span className={`status-dot ${healthError ? "status-dot--error" : health ? "status-dot--live" : ""}`} />
              <div>
                <strong>{backendLabel}</strong>
                <span>{healthError || `${indexedRecords} indexed records available`}</span>
              </div>
            </div>
          </div>

          <div className="quick-actions">
            <span className="quick-label">Try one of these</span>
            <div className="chip-row">
              {QUICK_SEARCHES.map((value) => (
                <button className="quick-chip" type="button" key={value} onClick={() => setQuery(value)}>
                  {value}
                </button>
              ))}
            </div>
          </div>
        </div>

      </header>

      <main className="workspace-grid">
        <section className="panel search-panel">
          <SectionHeader
            title="Search medicines by intent or symptom"
            description="Type a symptom, use case, or medicine fragment and let the vector search rank matching records."
          />

          <form className="search-form" onSubmit={onSearch}>
            <label className="search-query-label" htmlFor="search-query">Query</label>
            <div className="search-input-row">
              <input
                id="search-query"
                className="search-query-input"
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Try: fever medicine, cough syrup, acidity relief"
              />

              <div className="stepper-field stepper-field--compact stepper-field--inline" aria-label="Top K selector">
                <span className="stepper-label" title="Top K">
                  K <strong>{topK}</strong>
                </span>
                <div className="stepper-controls">
                  <button type="button" className="stepper-button" onClick={() => updateTopK(1)} aria-label="Increase top K">
                    ▲
                  </button>
                  <button type="button" className="stepper-button" onClick={() => updateTopK(-1)} aria-label="Decrease top K">
                    ▼
                  </button>
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={!canSearch}>
                {searchLoading ? "Searching..." : "Search medicines"}
              </button>
            </div>
          </form>

          {searchError ? <p className="error-banner">{searchError}</p> : null}

          {searchLoading ? (
            <div className="result-grid">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : searchResults.length > 0 ? (
            <div className="result-grid">
              {searchResults.map((item, index) => (
                <ResultCard key={`${item.name || "search-result"}-${item.score ?? index}`} item={item} />
              ))}
            </div>
          ) : (
            <EmptyState
              title={searchTouched ? "No matches found" : "Start with a natural-language search"}
              description={
                searchTouched
                  ? "Try a broader symptom, another dosage cue, or a different medicine phrase."
                  : "The UI is ready. Search by symptom, condition, or medicine name to see ranked results."
              }
            />
          )}
        </section>

        <section className="panel stack-panel">
          <SectionHeader
            eyebrow="Medicine details"
            title="Open a specific medicine profile"
            description="Lookup a medicine by name to get the full detail payload and safety note in a cleaner card layout."
          />

          <form className="stack-form" onSubmit={onDetails}>
            <div className="field">
              <label htmlFor="details-name">Medicine name</label>
              <input
                id="details-name"
                type="text"
                value={medicineName}
                onChange={(event) => setMedicineName(event.target.value)}
                placeholder="Enter an exact medicine name"
              />
            </div>

            <div className="chip-row chip-row--tight">
              {QUICK_MEDS.map((value) => (
                <button className="quick-chip quick-chip--small" type="button" key={value} onClick={() => setMedicineName(value)}>
                  {value}
                </button>
              ))}
            </div>

            <button className="primary-button" type="submit" disabled={!canDetails}>
              {detailsLoading ? "Loading details..." : "Get details"}
            </button>
          </form>

          {detailsError ? <p className="error-banner">{detailsError}</p> : null}

          {detailsLoading ? (
            <SkeletonCard />
          ) : detailsResult ? (
            <ResultCard item={detailsResult} />
          ) : (
            <EmptyState
              title={detailsTouched ? "No profile loaded" : "Ready when you are"}
              description={
                detailsTouched
                  ? "Try the exact medicine name again, or use one of the quick examples above."
                  : "Load a medicine profile to see composition, uses, side effects, dosage values, and the safety note."
              }
            />
          )}
        </section>

        <section className="panel stack-panel">
          <SectionHeader
            eyebrow="Similar medicines"
            title="Find alternatives around one medicine"
            description="This lane reuses the same vector index to surface near-neighbor recommendations for a selected medicine."
          />

          <form className="stack-form" onSubmit={onRecommend}>
            <div className="field">
              <label htmlFor="recommend-name">Seed medicine</label>
              <input
                id="recommend-name"
                type="text"
                value={recommendName}
                onChange={(event) => setRecommendName(event.target.value)}
                placeholder="Enter a medicine name to find similar options"
              />
            </div>

            <div className="chip-row chip-row--tight">
              {QUICK_MEDS.map((value) => (
                <button className="quick-chip quick-chip--small" type="button" key={`${value}-recommend`} onClick={() => setRecommendName(value)}>
                  {value}
                </button>
              ))}
            </div>

            <button className="primary-button" type="submit" disabled={!canRecommend}>
              {recommendLoading ? "Finding recommendations..." : "Recommend similar"}
            </button>
          </form>

          {recommendError ? <p className="error-banner">{recommendError}</p> : null}

          {recommendLoading ? (
            <div className="result-grid">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : recommendResults.length > 0 ? (
            <div className="result-grid">
              {recommendResults.map((item, index) => (
                <ResultCard key={`${item.name || "recommendation"}-${item.score ?? index}`} item={item} />
              ))}
            </div>
          ) : (
            <EmptyState
              title={recommendTouched ? "No recommendations returned" : "Try a medicine name to compare alternatives"}
              description={
                recommendTouched
                  ? "The catalog may not contain a close enough neighbor for that name. Try another medicine."
                  : "Similar medicines appear once the app can anchor a known medicine name."
              }
            />
          )}
        </section>
      </main>
    </div>
  );
}