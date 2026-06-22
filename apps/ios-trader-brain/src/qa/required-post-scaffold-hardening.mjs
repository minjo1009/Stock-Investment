const command = process.argv[2] ?? "unknown";

console.error(
  `[REQUIRED_POST_SCAFFOLD_HARDENING] ${command} is declared but not runnable in Task3804.`
);
console.error(
  "Finalize this command in Task3805 after Storybook/lint/test/screenshot tooling is installed."
);

process.exit(1);
