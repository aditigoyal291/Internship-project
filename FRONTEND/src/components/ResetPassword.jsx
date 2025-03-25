import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    if (!token) {
      setError("Reset token is missing. Please request a new password reset.");
      setIsSubmitting(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      setIsSubmitting(false);
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      setIsSubmitting(false);
      return;
    }

    try {
      console.log("Sending reset request with token:", token);

      const response = await axios.post(
        "http://localhost:8080/auth-password/reset",
        {
          token,
          newPassword,
        }
      );

      if (response.data.success) {
        setSuccess("Password reset successful! Redirecting to login...");
        // Redirect to login after a short delay with a message
        setTimeout(() => {
          navigate("/login", {
            state: {
              notification:
                "Password has been reset successfully. Please log in with your new password.",
            },
          });
        }, 2000);
      } else {
        setError(response.data.message || "An error occurred.");
        setIsSubmitting(false);
      }
    } catch (err) {
      console.error("Reset error details:", err.response?.data);
      setError(
        err.response?.data?.message ||
          "Invalid or expired token. Please request a new password reset."
      );
      setIsSubmitting(false);
    }
  };

  const toggleNewPasswordVisibility = () => {
    setShowNewPassword(!showNewPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white shadow-lg rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold text-center mb-4">
          Reset Your Password
        </h2>

        {error && (
          <p className="text-red-500 text-sm text-center mb-4">{error}</p>
        )}
        {success && (
          <p className="text-green-500 text-sm text-center mb-4">{success}</p>
        )}

        <form onSubmit={handleResetPassword} className="space-y-4">
          <div>
            <label className="block text-gray-600 font-medium">
              New Password
            </label>
            <div className="relative">
              <input
                type={showNewPassword ? "text" : "password"}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:ring-blue-300"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                required
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700"
                onClick={toggleNewPasswordVisibility}
                disabled={isSubmitting}
              >
                {showNewPassword ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M13.359 11.238C15.064 9.856 16 8 16 8s-3-5.5-8-5.5S0 8 0 8s.939 1.856 2.641 3.238l-.708.708C.942 10.732 0 9.075 0 8s3-6.5 8-6.5S16 6.925 16 8s-.942 2.732-2.929 3.945l-.708-.708zM8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6" />
                    <path d="M7 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0m1.5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m-5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m8 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m-4 4a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0" />
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M10.79 12.912l-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7.029 7.029 0 0 0 2.79-.588zM5.21 3.088A7.028 7.028 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474L5.21 3.089z" />
                    <path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829l-2.83-2.829zm4.95.708l-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6l-12-12 .708-.708 12 12-.708.708z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-gray-600 font-medium">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:ring-blue-300"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                required
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700"
                onClick={toggleConfirmPasswordVisibility}
                disabled={isSubmitting}
              >
                {showConfirmPassword ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M13.359 11.238C15.064 9.856 16 8 16 8s-3-5.5-8-5.5S0 8 0 8s.939 1.856 2.641 3.238l-.708.708C.942 10.732 0 9.075 0 8s3-6.5 8-6.5S16 6.925 16 8s-.942 2.732-2.929 3.945l-.708-.708zM8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6" />
                    <path d="M7 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0m1.5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m-5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m8 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m-4 4a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0m5 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0" />
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M10.79 12.912l-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7.029 7.029 0 0 0 2.79-.588zM5.21 3.088A7.028 7.028 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474L5.21 3.089z" />
                    <path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829l-2.83-2.829zm4.95.708l-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6l-12-12 .708-.708 12 12-.708.708z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className={`w-full ${
              isSubmitting ? "bg-blue-300" : "bg-blue-500 hover:bg-blue-600"
            } text-white py-2 rounded-lg transition duration-200`}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Resetting..." : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
