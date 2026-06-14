import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { login, register } from "../../api/auth";
import { ApiError } from "../../api/client";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { FormField } from "../../components/FormField";
import { useAuth } from "./useAuth";

export function RegisterPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    async mutationFn() {
      await register({ email, password });
      return login({ email, password });
    },
    onSuccess(tokens) {
      auth.setTokens(tokens);
      navigate("/links", { replace: true });
    },
  });

  if (auth.isAuthenticated) {
    return <Navigate to="/links" replace />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <main className="auth-shell">
      <Card title="Create account">
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField
            label="Email"
            name="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <FormField
            label="Password"
            name="password"
            type="password"
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {mutation.error && (
            <p className="form-error">{errorMessage(mutation.error)}</p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating account" : "Create account"}
          </Button>
          <p className="muted">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </Card>
    </main>
  );
}

function errorMessage(error: Error): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Unable to register. Please try again.";
}
