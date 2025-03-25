<script>
  import Nav from './Nav.svelte';
  import { auth, login, fetchUserInfo } from './auth.js';

  let username = '';
  let password = '';
  let message = '';
  let loading = false;

  // Check if user is already logged in
  fetchUserInfo();

  async function handleLogin() {
    loading = true;
    message = '';

    const result = await login(username, password);

    if (result.success) {
      message = 'Login successful!';
    } else {
      message = result.error;
    }

    loading = false;
  }
</script>

<div>
  <Nav />
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
</div>

<style>
  main {
    margin: 0 auto;
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
