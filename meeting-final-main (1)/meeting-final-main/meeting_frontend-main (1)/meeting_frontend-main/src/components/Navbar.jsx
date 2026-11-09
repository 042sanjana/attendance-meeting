import { Link } from "react-router-dom";
import "./Navbar.css"

function Navbar() {

  return (

    <nav className="navbar">

      <h2>
        AI Meeting Notes
      </h2>

      <div>

        <Link to="/dashboard">
          Dashboard
        </Link>

        {" | "}

        <Link to="/upload">
          Upload
        </Link>

        {" | "}

        <Link to="/history">
          History
        </Link>

      </div>

    </nav>

  );
}

export default Navbar;