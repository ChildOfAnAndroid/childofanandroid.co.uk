<template>
  <nav class="right-nav-column">
    <router-link to="/">index</router-link>
    <router-link to="/test">test</router-link>
  </nav>
</template>

<style scoped>
.right-nav-column {
  /* Layout and Sizing */
  display: flex;
  flex-direction: row;         /* vertical stacking for writing-mode */
  justify-content: flex-start; /* start at top */
  width: var(--nav-width);
  writing-mode: vertical-rl;
  flex-shrink: 1;
  text-align: var(--font-align);
  gap: 0;
  padding: 0;
  background-color: var(--panel-colour);
  border-left: var(--border-width) solid var(--border-colour);
  z-index: var(--nav-z);
  font-size: var(--font-size);
  line-height: var(--line-height);
}

a {
  padding: var(--padding);
  border-radius: var(--border-radius);
  font-weight: bold;
  color: var(--font-colour);
  text-decoration: none;
  text-shadow: var(--font-shadow);
  transition: background-color var(--transition-time) ease-in-out;
}

/* special class vue router adds to the link of the page you are currently on */
a.router-link-exact-active {
  background-color: var(--bg-colour);   /* blend into main page bg */
  border: var(--border);
  border-left-color: var(--bg-colour);  /* makes it look joined to panel bg */
  margin-left: calc(-1 * var(--border-width));
  padding-left: calc(var(--padding) + var(--border-width));
  box-shadow: calc(var(--border-width) * -1) 0 var(--bg-colour);
  color: var(--accent-colour);
  z-index: var(--tab-z);
}

a:hover {background-color: rgba(255, 255, 255, 0.05);}

/* hover */
.right-nav-column a:hover {border-color: var(--accent-colour);}
</style>