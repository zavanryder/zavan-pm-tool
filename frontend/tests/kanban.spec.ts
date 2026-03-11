import { expect, test, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/");
  await page.getByTestId("username-input").fill("user");
  await page.getByTestId("password-input").fill("password");
  await page.getByTestId("submit-button").click();
  await expect(page.getByRole("heading", { name: "Your Boards" })).toBeVisible();
}

async function openFirstBoard(page: Page) {
  await login(page);
  await page.getByTestId("open-board-1").click();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
}

async function addCard(page: Page, columnTestId: string, title: string, details: string) {
  const column = page.getByTestId(columnTestId);
  await column.getByRole("button", { name: /add a card/i }).click();
  await column.getByPlaceholder("Card title").fill(title);
  await column.getByPlaceholder("Details").fill(details);
  await column.getByRole("button", { name: /add card/i }).click();
  await expect(column.getByText(title)).toBeVisible();
}

test("loads the kanban board after login", async ({ page }) => {
  await openFirstBoard(page);
  await expect(page.getByTestId("board-name")).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await openFirstBoard(page);
  const name = `E2E Card ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const countBefore = await firstColumn.locator('[data-testid^="card-"]').count();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(name);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(name)).toBeVisible();
  await expect(firstColumn.locator('[data-testid^="card-"]')).toHaveCount(countBefore + 1);
});

test("moves a card between columns via drag and drop", async ({ page }) => {
  await openFirstBoard(page);

  // Add a fresh card to column 2 (Discovery) so we have a known card to drag
  const cardName = `DnD Test ${Date.now()}`;
  await addCard(page, "column-2", cardName, "drag me");

  const sourceColumn = page.getByTestId("column-2");
  const targetColumn = page.getByTestId("column-4");

  const card = sourceColumn.getByText(cardName).locator("../..");
  const dragHandle = card.getByLabel("Drag handle");
  const handleBox = await dragHandle.boundingBox();
  const targetBox = await targetColumn.boundingBox();
  if (!handleBox || !targetBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  const sourceCountBefore = await sourceColumn.locator('[data-testid^="card-"]').count();

  await page.mouse.move(
    handleBox.x + handleBox.width / 2,
    handleBox.y + handleBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    targetBox.x + targetBox.width / 2,
    targetBox.y + targetBox.height / 2,
    { steps: 20 }
  );
  await page.mouse.up();

  // Verify the source column lost a card
  await expect(sourceColumn.locator('[data-testid^="card-"]')).toHaveCount(
    sourceCountBefore - 1,
    { timeout: 5000 }
  );

  // Verify the card text appears in the target column
  await expect(targetColumn.getByText(cardName)).toBeVisible({ timeout: 5000 });
});
