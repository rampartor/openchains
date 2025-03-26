import { writable } from 'svelte/store';

// Create auth store
export const auth = writable({
  token: localStorage.getItem('token') || null,
  user: null,
  isAdmin: false,
  isAuthenticated: !!localStorage.getItem('token')
});

// Initialize auth if token exists
if (localStorage.getItem('token')) {
  fetchUserInfo();
}

// Fetch user info from API
export async function fetchUserInfo() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const response = await fetch('http://localhost:8000/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const userData = await response.json();
      // Also store the user data in localStorage to help with page refreshes
      localStorage.setItem('userData', JSON.stringify(userData));

      auth.update(state => ({
        ...state,
        user: userData,
        isAdmin: userData.role === 'admin',
        isAuthenticated: true
      }));
      return userData;
    } else {
      // If token is invalid, logout
      logout();
    }
  } catch (error) {
    console.error('Error fetching user info:', error);
  }
}

// Login function
export async function login(username, password) {
  try {
    const response = await fetch('http://localhost:8000/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (response.ok && data.access_token) {
      // Store token
      localStorage.setItem('token', data.access_token);

      // Update auth store
      auth.update(state => ({
        ...state,
        token: data.access_token,
        isAuthenticated: true
      }));

      // Get user data
      await fetchUserInfo();

      return { success: true };
    } else {
      return {
        success: false,
        error: data.detail || 'Invalid login attempt'
      };
    }
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: 'Network error or server unreachable'
    };
  }
}

// Logout function
export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('userData');

  auth.set({
    token: null,
    user: null,
    isAdmin: false,
    isAuthenticated: false
  });
}
