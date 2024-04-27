

class MinerRules:

    @staticmethod
    def should_reset_hours(block_count: int):
        return block_count <= 0

