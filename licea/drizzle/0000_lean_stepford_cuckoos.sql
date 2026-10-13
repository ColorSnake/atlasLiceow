CREATE TABLE `annual_snapshots` (
	`year` integer PRIMARY KEY NOT NULL,
	`payload` text NOT NULL,
	`revision` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `import_drafts` (
	`id` text PRIMARY KEY NOT NULL,
	`payload` text NOT NULL,
	`created` integer NOT NULL
);
