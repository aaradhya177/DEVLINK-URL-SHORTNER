import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listLinks } from "../../api/links";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorState, LoadingState } from "../../components/State";
import { CreateLinkForm } from "./CreateLinkForm";
import { LinksTable } from "./LinksTable";

const PAGE_SIZE = 25;

export function LinksDashboardPage() {
  const [page, setPage] = useState(0);
  const query = useQuery({
    queryKey: ["links", page],
    queryFn: () =>
      listLinks({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  });

  return (
    <div className="page-stack">
      <div className="page-title">
        <div>
          <h1>Links</h1>
          <p>Create, inspect, and manage active short links.</p>
        </div>
      </div>
      <Card title="Create link">
        <CreateLinkForm />
      </Card>
      <Card
        title="Your links"
        actions={
          <div className="pagination">
            <Button
              variant="secondary"
              onClick={() => setPage((value) => Math.max(0, value - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <span>Page {page + 1}</span>
            <Button
              variant="secondary"
              onClick={() => setPage((value) => value + 1)}
              disabled={!query.data || query.data.length < PAGE_SIZE}
            >
              Next
            </Button>
          </div>
        }
      >
        {query.isLoading && <LoadingState label="Loading links" />}
        {query.isError && <ErrorState message="Unable to load links." />}
        {query.data && <LinksTable links={query.data} />}
      </Card>
    </div>
  );
}
