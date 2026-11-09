import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./Login.css";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const login = async () => {

    if (!email || !password) {

      setError(
        "All fields are required"
      );

      return;
    }

    try {

      const response =
        await fetch(
          "http://127.0.0.1:8000/auth/login",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json"
            },
            body: JSON.stringify({
              email,
              password
            })
          }
        );

      const data =
        await response.json();

      console.log(
        "Response:",
        data
      );

      if (!response.ok) {

        setError(
          data.detail ||
          "Login failed"
        );

        return;
      }

      localStorage.setItem(
        "user",
        JSON.stringify(
          data.user
        )
      );

      localStorage.setItem(
        "userId",
        data.user.id
      );

      console.log(
        "Saved User:",
        data.user
      );

      console.log(
        "Saved User ID:",
        data.user.id
      );
      localStorage.setItem("token",data.access_token)
      navigate(
        "/dashboard"
      );

    } catch (error) {

      console.error(error);

      setError(
        "Server Error"
      );

    }

  };

  return (

    <div className="auth-container">

      <div className="auth-card">

        <h1>
          AI Meeting Notes
        </h1>

        <p>
          Authorized Office Meetings
        </p>

        {error && (

          <div className="error">
            {error}
          </div>

        )}

        <input
          type="email"
          placeholder="Corporate Email"
          value={email}
          onChange={(e) =>
            setEmail(
              e.target.value
            )
          }
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
        />

        <button
          onClick={login}
        >
          Login
        </button>

        <div className="switch-link">

          New User?

          <Link to="/register">
            Register
          </Link>

        </div>

      </div>

    </div>

  );
}

export default Login;