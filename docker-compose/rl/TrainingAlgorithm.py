class TrainingAlgorithm:
    def __init__(self):
        pass

    def prepare_model(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `prepare_model` in {self}")

    def before_episode(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `before_episode` in {self}")

    def before_action(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `before_action` in {self}")

    def take_action(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `take_action` in {self}")

    def before_step(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `before_step` in {self}")

    def after_step(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `after_step` in {self}")

    def handle_gameover(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `handle_gameover` in {self}")

    def after_episode(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `after_episode` in {self}")

    def before_cleanup(self, *args, **kwargs):
        raise NotImplementedError(f"You need to implement method `before_cleanup` in {self}")

    def __str__(self):
        return "TrainingAlgorithm Abstract Class"
    