// Lets a component side-effect-import a plain .css file (e.g. a
// third-party library's stylesheet) so the bundler scopes it to that
// component's chunk instead of the global styles.css — see doctors-list.ts
// importing ag-grid's CSS instead of listing it in angular.json's global
// `styles` array.
declare module '*.css';
