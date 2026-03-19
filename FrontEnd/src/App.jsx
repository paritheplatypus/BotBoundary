import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import Register from "./pages/Register";
import SessionDetail from "./pages/SessionDetail";

export default function App() {
  return (
    <div className="page">
      <Navbar />
      <div className="page-content">
        <Routes>
          <Route path="/"                   element={<Login />} />
          <Route path="/about"              element={<About />} />
          <Route path="/dashboard"          element={<Dashboard />} />
          <Route path="/register"           element={<Register />} />
          <Route path="/session/:sessionId" element={<SessionDetail />} />
        </Routes>
      </div>
    </div>
  );
}
