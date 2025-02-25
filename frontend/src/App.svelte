<script>
  let username = "";
  let password = "";
  let message = "";

  async function handleLogin() {
    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        message = data.message;
      } else {
        const errData = await response.json();
        message = errData.detail || "Invalid login attempt";
      }
    } catch (error) {
      message = "Network error";
    }
  }
</script>

<main>
  <h1>Login</h1>
  <form on:submit|preventDefault={handleLogin}>
    <label for="username">Username:</label>
    <input
      id="username"
      type="text"
      bind:value={username}
      placeholder="Enter username"
    />
    <br /><br />

    <label for="password">Password:</label>
    <input
      id="password"
      type="password"
      bind:value={password}
      placeholder="Enter password"
    />
    <br /><br />

    <button type="submit">Login</button>
  </form>

  <p>{message}</p>
</main>

<style>
  main {
    margin: 2rem auto;
    max-width: 400px;
  }

  label {
    display: inline-block;
    width: 6rem;
  }

  input {
    margin-bottom: 1rem;
  }
</style>