import { NavLink } from "react-router-dom";
import "../styles/navbar.css";

export default function Navbar() {
  return (
   <nav className="navbar">
  <div className="navbar-inner">
    <div className="logo">CacheMeOutside</div>

    <div className="nav-links">
    <NavLink to="/">Login</NavLink>
    <NavLink to="/about">About</NavLink>
    <NavLink to="/dashboard">Dashboard</NavLink>
    </div>

    <div className="status">● System active</div>
  </div>
</nav>
  );
}