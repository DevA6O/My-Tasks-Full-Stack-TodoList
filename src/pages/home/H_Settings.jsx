import React, { useEffect, useState } from "react";
import Modal from "../../components/Modal";
import { FiMail, FiUser, FiLock } from "react-icons/fi";
import { useAuth } from "../../context/AuthContext";
import { toast } from "react-toastify";
import LoadingScreen from "../../components/LoadingScreen";

export default function HomePageSettingsModal({ isOpen, onClose }) {
    const { accessToken, loading: authLoading } = useAuth();

    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [sessions, setSessions] = useState([]);
    const [onUpdate, setOnUpdate] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Safety-related
        if (authLoading || !isOpen) return;

        if (!accessToken && !authLoading) {
            window.location.href = "/login";
            return;
        };

        // Get informations from backend to display
        async function getInformations() {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_URL}/settings/service`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${accessToken}`
                    }
                });

                setLoading(false);

                if (response.ok) {
                    const data = await response.json();

                    setUsername(data.informations.username);
                    setEmail(data.informations.email);
                    setSessions(data.informations.sessions);
                } else {
                    onClose();
                    toast.error("Settings is not accessible: Please try again later.");
                };
            } finally {
                setOnUpdate(false);
            }
        };

        getInformations();
    }, [isOpen, onUpdate])

    const handleSave = () => {
        alert("Changes saved");
    };

    const removeSession = async (jti_id) => {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/settings/session/revoke`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            },
            body: JSON.stringify({jti_id: jti_id})
        });

        if (response.ok) {
            setOnUpdate(true);
        }
    };

    return (
        <>
            {isOpen && loading && <LoadingScreen />}

            <Modal isOpen={isOpen} onClose={onClose} classname="h-full overflow-auto">
                <div className="max-w-3xl mx-auto p-6 sm:p-10 space-y-10 bg-gray-50 min-h-screen">
                    <button
                        onClick={onClose}
                        className="text-sm text-blue-600 hover:underline flex items-center"
                    >
                        ← Back
                    </button>

                    <h1 className="text-3xl font-bold text-gray-800">Settings</h1>

                    {/* Profile */}
                    <section className="bg-white shadow rounded-lg p-6 sm:p-8 space-y-6 border border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-800">Profile-Settings</h2>

                        {/* Username */}
                        <div className="relative">
                            <label htmlFor="newUsername" className="block text-sm font-medium text-gray-600 mb-1">
                                Username
                            </label>
                            <div className="flex items-center border rounded-md px-3 py-2 focus-within:ring-2 focus-within:ring-blue-500">
                                <FiUser className="text-gray-400 mr-2" />
                                <input
                                    id="newUsername"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full focus:outline-none"
                                    placeholder="Nutzername"
                                />
                            </div>
                        </div>

                        {/* Email */}
                        <div className="relative">
                            <label htmlFor="newEmail" className="block text-sm font-medium text-gray-600 mb-1">
                                E-Mail
                            </label>
                            <div className="flex items-center border rounded-md px-3 py-2 focus-within:ring-2 focus-within:ring-blue-500">
                                <FiMail className="text-gray-400 mr-2" />
                                <input
                                    id="newEmail"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full focus:outline-none"
                                    placeholder="E-Mail-Adresse"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="relative">
                            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-600 mb-1">
                                Password
                            </label>
                            <div className="flex items-center border rounded-md px-3 py-2 focus-within:ring-2 focus-within:ring-blue-500">
                                <FiLock className="text-gray-400 mr-2" />
                                <input
                                    id="newPassword"
                                    type="password"
                                    className="w-full focus:outline-none"
                                    placeholder="New Password"
                                />
                            </div>
                        </div>

                        <button
                            onClick={handleSave}
                            className="bg-blue-600 text-white px-5 py-2.5 rounded-md cursor-pointer hover:bg-blue-700 transition duration-150"
                        >
                            Save changes
                        </button>
                    </section>

                    {/* Sessions */}
                    <section className="bg-white shadow rounded-lg p-6 sm:p-8 border border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-800 mb-4">Active sessions</h2>

                        {sessions.length === 0 ? (
                            <p className="text-gray-500 text-sm">No active sessions found.</p>
                        ) : (
                            <ul className="space-y-4">
                                {sessions.map((session) => (
                                    <li
                                        key={session.jti_id}
                                        className={`flex justify-between items-center p-4 rounded-md border transition ${
                                            session.current
                                                ? "border-blue-500 bg-blue-50"
                                                : "border-gray-200 bg-white hover:bg-gray-50"
                                        }`}
                                    >
                                        <div>
                                            <p className="font-medium text-gray-800">
                                                {session.browser} – {session.os}
                                            </p>
                                            <p className="text-sm text-gray-500">{session.ip_address}</p>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {session.current ? (
                                                <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
                                                    This session
                                                </span>
                                            ) : (
                                                <button
                                                    onClick={() => removeSession(session.jti_id)}
                                                    className="text-sm text-red-600 hover:underline"
                                                >
                                                    Log out
                                                </button>
                                            )}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </section>
                </div>
            </Modal>
        </>
    );
}
