import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";
import { createLink, getQrImageUrl } from "../../api/links";
import { apiUrl } from "../../api/client";
import { Button } from "../../components/Button";
import { FormField } from "../../components/FormField";

export function CreateLinkForm() {
  const queryClient = useQueryClient();
  const [destinationUrl, setDestinationUrl] = useState("");
  const [customAlias, setCustomAlias] = useState("");
  const [title, setTitle] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [isProtected, setIsProtected] = useState(false);
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: createLink,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ["links"] });
      setDestinationUrl("");
      setCustomAlias("");
      setTitle("");
      setExpiresAt("");
      setIsProtected(false);
      setPassword("");
    },
  });

  const previewUrl = useMemo(() => {
    if (!customAlias.trim()) {
      return apiUrl("/r/preview");
    }
    return apiUrl(`/r/${customAlias.trim()}`);
  }, [customAlias]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate({
      destination_url: destinationUrl,
      title: title || null,
      custom_alias: customAlias || null,
      password: isProtected ? password : null,
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      strip_tracking_params: true,
    });
  }

  return (
    <form className="create-grid" onSubmit={handleSubmit}>
      <div className="form-grid">
        <FormField
          label="Long URL"
          type="url"
          value={destinationUrl}
          onChange={(event) => setDestinationUrl(event.target.value)}
          required
        />
        <FormField
          label="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Launch post"
        />
        <FormField
          label="Custom alias"
          value={customAlias}
          onChange={(event) => setCustomAlias(event.target.value)}
          placeholder="spring-launch"
        />
        <FormField
          label="Expiration"
          type="datetime-local"
          value={expiresAt}
          onChange={(event) => setExpiresAt(event.target.value)}
        />
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={isProtected}
            onChange={(event) => setIsProtected(event.target.checked)}
          />
          Password protect this link
        </label>
        {isProtected && (
          <FormField
            label="Link password"
            type="password"
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        )}
        {mutation.error && (
          <p className="form-error">Unable to create link. Check the URL and alias.</p>
        )}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating" : "Create link"}
        </Button>
      </div>
      <div className="qr-preview">
        <QRCodeCanvas value={previewUrl} size={132} />
        <p>QR preview updates when you enter a custom alias.</p>
        {customAlias.trim() && (
          <small>
            Downloadable QR: {getQrImageUrl(customAlias.trim(), "png")}
          </small>
        )}
      </div>
    </form>
  );
}
