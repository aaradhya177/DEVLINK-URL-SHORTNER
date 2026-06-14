import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getAnalyticsSummary,
  getDeviceBreakdown,
  getGeoBreakdown,
  getTimeseries,
} from "../../api/analytics";
import { Card } from "../../components/Card";
import { ErrorState, LoadingState } from "../../components/State";

export function AnalyticsPage() {
  const params = useParams();
  const linkId = Number(params.linkId);
  const range = useMemo(() => defaultRange(), []);

  const summaryQuery = useQuery({
    queryKey: ["analytics", linkId, "summary"],
    queryFn: () => getAnalyticsSummary(linkId),
    enabled: Number.isFinite(linkId),
  });
  const timeseriesQuery = useQuery({
    queryKey: ["analytics", linkId, "timeseries", range.from, range.to],
    queryFn: () => getTimeseries(linkId, range.from, range.to),
    enabled: Number.isFinite(linkId),
  });
  const geoQuery = useQuery({
    queryKey: ["analytics", linkId, "geo"],
    queryFn: () => getGeoBreakdown(linkId),
    enabled: Number.isFinite(linkId),
  });
  const devicesQuery = useQuery({
    queryKey: ["analytics", linkId, "devices"],
    queryFn: () => getDeviceBreakdown(linkId),
    enabled: Number.isFinite(linkId),
  });

  if (!Number.isFinite(linkId)) {
    return <ErrorState message="Invalid link ID." />;
  }

  return (
    <div className="page-stack">
      <div className="page-title">
        <div>
          <h1>Analytics</h1>
          <p>Dashboard metrics for link #{linkId}.</p>
        </div>
      </div>
      <div className="metric-grid">
        <Card title="Total clicks">
          {summaryQuery.isLoading && <LoadingState />}
          {summaryQuery.isError && <ErrorState message="Unable to load summary." />}
          {summaryQuery.data && (
            <strong className="metric">{summaryQuery.data.total_clicks}</strong>
          )}
        </Card>
        <Card title="Unique clicks">
          {summaryQuery.data ? (
            <>
              <strong className="metric">N/A</strong>
              <p className="muted">{summaryQuery.data.unique_clicks_note}</p>
            </>
          ) : (
            <LoadingState />
          )}
        </Card>
      </div>
      <Card title="Clicks over time">
        {timeseriesQuery.isLoading && <LoadingState label="Loading chart" />}
        {timeseriesQuery.isError && <ErrorState message="Unable to load chart." />}
        {timeseriesQuery.data && (
          <div className="chart">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={timeseriesQuery.data.points}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="clicks" stroke="#2563eb" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
      <div className="split-grid">
        <Card title="Countries">
          {geoQuery.isLoading && <LoadingState />}
          {geoQuery.isError && <ErrorState message="Unable to load countries." />}
          {geoQuery.data && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={geoQuery.data.items}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="dimension" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="clicks" fill="#16a34a" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
        <Card title="Devices">
          {devicesQuery.isLoading && <LoadingState />}
          {devicesQuery.isError && <ErrorState message="Unable to load devices." />}
          {devicesQuery.data && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Device</th>
                    <th>Browser</th>
                    <th>OS</th>
                    <th>Clicks</th>
                  </tr>
                </thead>
                <tbody>
                  {devicesQuery.data.items.map((item) => (
                    <tr
                      key={`${item.device_type}-${item.browser}-${item.os}`}
                    >
                      <td>{item.device_type}</td>
                      <td>{item.browser}</td>
                      <td>{item.os}</td>
                      <td>{item.clicks}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - 30);
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  };
}
