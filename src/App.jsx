import React, { use } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { ToastContainer, Slide } from "react-toastify";
import LoadingScreen from "./components/LoadingScreen";

import Register from "./pages/auth/Register";
import Login from "./pages/auth/Login";
import HomePage from "./pages/home/homepage";

// Suitable to create a private route
function PrivateRoute({ children }) {
  const { isAuth, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  };
  // Not logged in -> Forwarding to login page
  if (!isAuth) {
    return <Navigate to={"/login"} replace />;
  };
  return children;
};

// Suitable for Auth-Management
function AuthRoute({ children }) {
  const { isAuth, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  };
  // Already logged in -> forwarding to homepage
  if (isAuth) {
    return <Navigate to={"/"} replace />;
  };

  return children;
};


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/register" element={<AuthRoute><Register /></AuthRoute>} />
        <Route path="/login" element={<AuthRoute><Login /></AuthRoute>}/>

        <Route path="/" element={<HomePage />} />
      </Routes>

      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick={false}
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
        transition={Slide}
      />
    </BrowserRouter>
  );
}