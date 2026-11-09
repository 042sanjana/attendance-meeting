import { useState } from "react";
import "./Register.css";
import { Link, useNavigate } from "react-router-dom";

function Register() {
  const navigate=useNavigate();

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword,
    setConfirmPassword] =
    useState("");

  const [message,
    setMessage] =
    useState("");

   const register = async () => {

    if (
  !name ||
  !email ||
  !password ||
  !confirmPassword
) {

  setMessage(
    "All fields required"
  );

  return;
}

if (
  name.trim().length < 3
) {

  setMessage(
    "Name must be at least 3 characters"
  );

  return;
}

const emailRegex =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

if (
  !emailRegex.test(email)
) {

  setMessage(
    "Enter valid email"
  );

  return;
}

if (
  !email.endsWith("@mph.com")
) {

  setMessage(
    "Use corporate email (@mph.com)"
  );

  return;
}

if (
  password.length < 6
) {

  setMessage(
    "Password must be at least 6 characters"
  );

  return;
}

const passwordRegex =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/;

if (
  !passwordRegex.test(password)
) {

  setMessage(
    "Password must contain uppercase, lowercase and number"
  );

  return;
}

if (
  password !== confirmPassword
) {

  setMessage(
    "Passwords do not match"
  );

  return;
}
    try {

  const response =
    await fetch(
      "http://127.0.0.1:8000/auth/register",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json"
        },
        body: JSON.stringify({
          name,
          email,
          password
        })
      }
    );

  const data =
    await response.json();

  console.log(data);

   
if (response.ok) {

  localStorage.setItem(
    "token",
    data.access_token
  );

  localStorage.setItem(
    "user",
    JSON.stringify(data.user)
  );

  localStorage.setItem(
    "userId",
    data.user.id
  );

  setMessage(
    "Registration Successful"
  );

  navigate("/dashboard");

}
  else{
    setMessage(data.detail)
  }
    } catch(error){
      setMessage("Server error");
    }
    };

  return (

    <div className="auth-container">

      <div className="auth-card">

        <h1>
          Register
        </h1>

        {message && (
          <div className="error">
            {message}
          </div>
        )}

        <input
          placeholder="Full Name"
          value={name}
          onChange={(e) =>
            setName(
              e.target.value
            )
          }
        />

        <input
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

        <input
          type="password"
          placeholder="Confirm Password"
          value={
            confirmPassword
          }
          onChange={(e) =>
            setConfirmPassword(
              e.target.value
            )
          }
        />


        
        <button
          onClick={register}
        >
          Register
        </button>


        <div className="switch-link">

          Already have account?

          <Link to="/">
            Login
          </Link>

        </div>

      </div>

    </div>

  );
}

export default Register;