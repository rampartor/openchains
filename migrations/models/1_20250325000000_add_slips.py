from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- Add card_number field to users table
    ALTER TABLE "users" ADD "card_number" VARCHAR(16);

    -- Create slips table
    CREATE TABLE IF NOT EXISTS "slips" (
        "id" SERIAL NOT NULL PRIMARY KEY,
        "card_number" VARCHAR(16) NOT NULL,
        "amount" DECIMAL(10,2) NOT NULL,
        "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    -- Create index on slips.card_number
    CREATE INDEX "idx_slips_card_number" ON "slips" ("card_number");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP TABLE IF EXISTS "slips";
    ALTER TABLE "users" DROP COLUMN "card_number";
    """
