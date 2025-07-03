import { loginUser, registerUser } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegisterLink = document.getElementById('showRegister');
    const showLoginLink = document.getElementById('showLogin');
    const errorMessageDiv = document.getElementById('errorMessage');

    // Check if already logged in
    if (localStorage.getItem('jwtToken')) {
        // If on index.html or root, redirect to master_list.html
        if (window.location.pathname === '/index.html' || window.location.pathname === '/') {
            window.location.href = 'master_list.html';
            return; // Stop further execution if redirecting
        }
    }

    function displayError(message) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.classList.remove('hidden');
    }

    function clearError() {
        errorMessageDiv.textContent = '';
        errorMessageDiv.classList.add('hidden');
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearError();
            const username = loginForm.username.value;
            const password = loginForm.password.value;

            try {
                const data = await loginUser({ username, password });
                if (data && data.access_token) {
                    localStorage.setItem('jwtToken', data.access_token);
                    window.location.href = 'master_list.html'; // Redirect to the main app page
                } else {
                    displayError('Login failed. No token received.');
                }
            } catch (error) {
                console.error('Login error:', error);
                displayError(error.message || 'Login failed. Please check your credentials.');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearError();
            const username = registerForm.username.value;
            const password = registerForm.password.value;
            const confirmPassword = registerForm.confirmPassword.value;

            if (password !== confirmPassword) {
                displayError('Passwords do not match.');
                return;
            }

            try {
                const user = await registerUser({ username, password });
                if (user && user.username) {
                    // Optionally, log them in directly or show a success message
                    alert('Registration successful! Please login.');
                    showLoginForm(); // Switch to login form
                } else {
                     displayError('Registration failed. Please try again.');
                }
            } catch (error) {
                console.error('Registration error:', error);
                displayError(error.message || 'Registration failed. Username might be taken or invalid data.');
            }
        });
    }

    function showRegistrationForm() {
        if (loginForm) loginForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('hidden');
        clearError();
    }

    function showLoginForm() {
        if (registerForm) registerForm.classList.add('hidden');
        if (loginForm) loginForm.classList.remove('hidden');
        clearError();
    }

    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            showRegistrationForm();
        });
    }

    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            showLoginForm();
        });
    }
});
