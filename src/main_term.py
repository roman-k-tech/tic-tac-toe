import asyncio
from settings import Settings


async def main() -> None:
    game = Settings().create_game(active_cell=True)
    with game:
        await game.run_game()


if __name__ == "__main__":
    with asyncio.Runner() as runner:
        runner.run(main())
