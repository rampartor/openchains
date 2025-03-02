<script>
  let username = '';
  let password = '';
  let message = '';
  let loading = false;

  async function handleLogin() {
    loading = true;
    message = '';

    try {
      const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        message = 'Login successful!';
        // Store the token in localStorage for future requests
        if (data.access_token) {
          localStorage.setItem('token', data.access_token);
        }
      } else {
        message = data.detail || 'Invalid login attempt';
      }
    } catch (error) {
      console.error('Login error:', error);
      message = 'Network error or server unreachable';
    } finally {
      loading = false;
    }
  }
</script>

<main>
  <h1>Login</h1>
  <form on:submit|preventDefault={handleLogin}>
    <div class="form-group">
      <label for="username">Username:</label>
      <input id="username" type="text" bind:value={username} placeholder="Enter username" required />
    </div>

    <div class="form-group">
      <label for="password">Password:</label>
      <input id="password" type="password" bind:value={password} placeholder="Enter password" required />
    </div>

    <button type="submit" disabled={loading}>
      {loading ? 'Logging in...' : 'Login'}
    </button>
  </form>

  {#if message}
    <div class="message" class:error={message.includes('error') || message.includes('Invalid')}>
      {message}
    </div>
  {/if}
</main>

<style>
  main {
    margin: 2rem auto;
    max-width: 400px;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    background-color: #2a2a2a;
  }

  h1 {
    text-align: center;
    margin-bottom: 2rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #333;
    color: #fff;
  }

  button {
    width: 100%;
    padding: 0.75rem;
    background-color: #4a56e2;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  button:hover:not(:disabled) {
    background-color: #3a46d2;
  }

  button:disabled {
    background-color: #666;
    cursor: not-allowed;
  }

  .message {
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 4px;
    background-color: #2e7d32;
    color: white;
    text-align: center;
  }

  .error {
    background-color: #c62828;
  }
</style>
