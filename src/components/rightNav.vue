<template>
	<nav class="right-nav-column">
		<router-link to="/">index</router-link>
		<router-link to="/paint">paint</router-link>
		<router-link to="/test">test</router-link>
	</nav>
</template>

<style scoped>
.right-nav-column {
	/* Layout and Sizing */
	display: flex;
	flex: 0 1 auto;							/* shrink if needed, grow if needed */
	width: var(--nav-width);
	flex-direction: row;				 /* vertical stacking for writing-mode */
	justify-content: flex-start; /* start at top */
	writing-mode: vertical-rl;
	flex-shrink: 0;
	text-align: var(--font-align);
	gap: 0;
	padding: 0;
	background-color: var(--panel-colour);
	border-left: var(--border-width) solid var(--border-colour);
	z-index: var(--nav-z);
	font-size: var(--font-size);
	line-height: var(--line-height);
	white-space: nowrap;	
}

a {
	padding: var(--padding);
	border: var(--border);
	border-color: var(--panel-colour);
	border-top-left-radius: 0;
	border-bottom-left-radius: 0;
	border-top-right-radius: var(--border-radius);
	border-bottom-right-radius: var(--border-radius);
	padding-left: calc(var(--padding) + var(--border-width));
	font-weight: bold;
	color: var(--font-colour);
	text-decoration: none;
	text-shadow: var(--font-shadow);
	transition: all var(--transition-time) ease-in-out;
}

/* special class vue router adds to the link of the page you are currently on */
a.router-link-exact-active {
	background-color: var(--bg-colour);	 /* blend into main page bg */
	border-color: var(--border-colour);
	border-left-color: var(--bg-colour);	/* makes it look joined to panel bg */
	margin-left: calc(-1 * var(--border-width));
	padding-left: calc(var(--padding) + var(--border-width));
	color: var(--accent-colour);
	z-index: var(--tab-z);
}

/* hover */
.right-nav-column a:hover {
	background-color: var(--border-colour);
	border-color: var(--accent-colour);
	border-left-color: var(--border-colour);
	margin-left: calc(-1 * var(--border-width));
	padding-left: calc(var(--padding) + var(--border-width));
	}
</style>