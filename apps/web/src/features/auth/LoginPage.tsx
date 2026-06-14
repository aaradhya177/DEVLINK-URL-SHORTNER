import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { login } from "../../api/auth";
import { ApiError } from "../../api/client";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { FormField } from "../../components/FormField";
import { useAuth } from "./useAuth";

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const from = (location.state as { from?: string } | null)?.from ?? "/links";

  const mutation = useMutation({
    mutationFn: login,
    onSuccess(tokens) {
      auth.setTokens(tokens);
      navigate(from, { replace: true });
    },
  });

  if (auth.isAuthenticated) {
    return <Navigate to="/links" replace />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate({ email, password });
  }

  return (
    <main className="auth-shell">
      <Card title="Sign in">
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
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {mutation.error && (
            <p className="form-error">{errorMessage(mutation.error)}</p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Signing in" : "Sign in"}
          </Button>
          <p className="muted">
            New here? <Link to="/register">Create an account</Link>
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
  return "Unable to sign in. Please try again.";
}
