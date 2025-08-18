<template>
        <div class="admin-page">
                <div v-if="!loggedIn" class="login-box">
                        <h2>Admin Login</h2>
                        <input type="password" v-model="password" placeholder="Password" />
                        <button @click="login">Login</button>
                </div>
                <div v-else class="files-box">
                        <h2>Storage Files</h2>
                        <pre>{{ files }}</pre>
                </div>
        </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const PASSWORD = 'cab.bo';
const password = ref('');
const loggedIn = ref(false);
const files = ref('');

async function login() {
        if (password.value === PASSWORD) {
                loggedIn.value = true;
                const res = await fetch('/api/files');
                const data = await res.json();
                files.value = JSON.stringify(data, null, 2);
        } else {
                alert('Incorrect password');
        }
}
</script>

<style scoped>
.admin-page {
        padding: 1rem;
}
.login-box, .files-box {
        max-width: 400px;
        margin: 0 auto;
}
pre {
        background: #eee;
        padding: 1rem;
        overflow-x: auto;
}
</style>