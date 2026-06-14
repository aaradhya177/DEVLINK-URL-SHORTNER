import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { deleteLink, updateLink } from "../../api/links";
import type { LinkResponse } from "../../api/types";
import { Button } from "../../components/Button";
import { EmptyState } from "../../components/State";
import { StatusBadge } from "../../components/StatusBadge";

export function LinksTable({ links }: { links: LinkResponse[] }) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: deleteLink,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["links"] }),
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, title }: { id: number; title: string | null }) =>
      updateLink(id, { title }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["links"] }),
  });

  if (links.length === 0) {
    return <EmptyState message="No links yet. Create one to start tracking." />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Short code</th>
            <th>Destination</th>
            <th>Status</th>
            <th>Expires</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {links.map((link) => (
            <tr key={link.id}>
              <td>
                <strong>{link.short_code}</strong>
                {link.is_password_protected && <span className="lock">Locked</span>}
              </td>
              <td>
                <input
                  className="table-input"
                  defaultValue={link.title ?? ""}
                  placeholder="Untitled"
                  onBlur={(event) => {
                    const nextTitle = event.target.value || null;
                    if (nextTitle !== link.title) {
                      updateMutation.mutate({ id: link.id, title: nextTitle });
                    }
                  }}
                />
                <a href={link.destination_url}>{link.destination_url}</a>
              </td>
              <td>
                <StatusBadge active={link.is_active} />
              </td>
              <td>{link.expires_at ? formatDate(link.expires_at) : "Never"}</td>
              <td>
                <div className="action-row">
                  <Link className="text-button" to={`/analytics/${link.id}`}>
                    Analytics
                  </Link>
                  <Button
                    variant="danger"
                    onClick={() => deleteMutation.mutate(link.id)}
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
