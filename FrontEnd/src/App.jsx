import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";

function About() {
  return <div style={{ padding: 40 }}>About page placeholder</div>;
}



export default function App() {
  return (
    <div className="page">
      <Navbar />

      <div className="page-content">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/about" element={<About />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </div>
  );
}