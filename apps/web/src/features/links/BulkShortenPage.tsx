import { useMutation } from "@tanstack/react-query";
import { ChangeEvent, FormEvent, useState } from "react";
import { bulkCreateLinks } from "../../api/links";
import type { BulkLinkCreateResponse } from "../../api/types";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorState, EmptyState } from "../../components/State";
import { TextareaField } from "../../components/TextareaField";

export function BulkShortenPage() {
  const [rawUrls, setRawUrls] = useState("");
  const mutation = useMutation({
    mutationFn: bulkCreateLinks,
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate({
      urls: parseUrls(rawUrls),
      strip_tracking_params: true,
    });
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setRawUrls(await file.text());
  }

  return (
    <div className="page-stack">
      <div className="page-title">
        <div>
          <h1>Bulk shorten</h1>
          <p>Process up to 50 URLs and keep item-level errors isolated.</p>
        </div>
      </div>
      <Card title="Input">
        <form className="form-grid" onSubmit={handleSubmit}>
          <TextareaField
            label="URLs or CSV"
            value={rawUrls}
            onChange={(event) => setRawUrls(event.target.value)}
            rows={10}
            placeholder="https://example.com&#10;https://docs.example.com"
            required
          />
          <FormUpload onChange={handleUpload} />
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Processing" : "Shorten URLs"}
          </Button>
        </form>
      </Card>
      <BulkResults data={mutation.data} error={mutation.error} />
    </div>
  );
}

function FormUpload({
  onChange,
}: {
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <label className="field">
      <span>CSV upload</span>
      <input type="file" accept=".csv,.txt" onChange={onChange} />
    </label>
  );
}

function BulkResults({
  data,
  error,
}: {
  data: BulkLinkCreateResponse | undefined;
  error: Error | null;
}) {
  if (error) {
    return <ErrorState message="Bulk request failed. Please try fewer URLs." />;
  }
  if (!data) {
    return <EmptyState message="Bulk results will appear here." />;
  }
  return (
    <Card title="Results">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>URL</th>
              <th>Status</th>
              <th>Short code</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((result) => (
              <tr key={result.index}>
                <td>{result.index + 1}</td>
                <td>{result.url}</td>
                <td>{result.status}</td>
                <td>{result.link?.short_code ?? ""}</td>
                <td>{result.error ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function parseUrls(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((entry) => entry.trim())
    .filter(Boolean)
    .slice(0, 50);
}
