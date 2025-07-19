import React, { createContext, useState, useContext, useEffect } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [accessToken, setAccessToken] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isAuth, setIsAuth] = useState(false);

    useEffect(() => {
        async function refreshToken() {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_URL}/refresh`, {
                    method: "POST",
                    credentials: "include",
                    headers: {"Content-Type": "application/json"}
                });

                if (response.ok) {
                    const data = await response.json()
                    setAccessToken(data.access_token);
                    setIsAuth(true);
                } else {
                    setAccessToken(null);
                    setIsAuth(false);
                };
            } catch {
                setIsAuth(false);
            } finally {
                setLoading(false);
            };
        };

        refreshToken();
    }, [])

    return (
        <AuthContext.Provider value={{ accessToken, setAccessToken, isAuth, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);