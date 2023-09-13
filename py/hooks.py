from __future__ import annotations
from typing import Any, Callable, Dict, List, Union
from dataclasses import dataclass, field

#internal modules
from db import Record


@dataclass(frozen=True)
class Hook:
    """Инкапсуляция логики хука"""
    name: str  # для реализации связывания по условиями "выполнит до" / "выполнить после"/ "выполнить вместо"
    method: Callable[[Hook.HookParams], Hook.HookParams]
    # сам знает, что выполняется перед ним, что после, а что вместо?
    handlers: Dict[str, List[Hook]] = field(default_factory=lambda: {
        'before': [],
        'instead': [],
        'after': [],
    })

    def __call__(self, params: HookParams) -> HookParams:
        params = self.__run_handlers_before(params)
        if self.handlers_instead:
            params = self.__run_handlers_instead(params)
        else:
            params = self.method(params)
        return self.__run_handlers_after(params)

    def add(self, name: str, method: Callable[[Hook.HookParams],
                                              Hook.HookParams],
            hook_type: str):
        """Добавить хук к хуку :)))))))))))"""
        # Неявно бросем KeyError, если пришел невалидный ключ
        target_hooks = self.handlers[hook_type]
        target_hooks.append(Hook(name, method))

    @property
    def handlers_before(self):
        """Список обработчиков, выполняемых перед хуком"""
        return self.handlers['before']

    @property
    def handlers_instead(self):
        """Список обработчиков, выполняемых вместо хука"""
        return self.handlers['instead']

    @property
    def handlers_after(self):
        """Список обработчиков, выполняемых после хука"""
        return self.handlers['after']

    def __run_handlers_before(self, params: Hook.HookParams) -> HookParams:
        """Запуск обработчиков, выполняемых перед хуком"""
        if params.before:
            params = self.__run_handlers(self.handlers_before, params)
        return params

    def __run_handlers_instead(self, params: Hook.HookParams) -> HookParams:
        """Запуск обработчиков, выполняемых вместо хука"""
        if params.instead:
            params = self.__run_handlers(self.handlers_instead, params)
        return params

    def __run_handlers_after(self, params: Hook.HookParams) -> HookParams:
        """Запуск обработчиков, выполняемых после хука"""
        if params.after:
            params = self.__run_handlers(self.handlers_after, params)
        return params

    @classmethod
    def __run_handlers(cls, handlers: List[Hook],
                       params: HookParams) -> HookParams:
        """Запуск обработчиков"""
        for hook in handlers:
            params = hook(params)
        return params

    @dataclass
    class HookParams:
        """Параметр хуков обработчиков"""
        args: Dict[str, Any] = field(default_factory=dict)
        skip: bool = False
        """Пропуск выполнение хука. Обработчики хука при этом выполняются"""
        before: bool = True
        instead: bool = True
        after: bool = True
        """Выполнять ли соответствующие обработчики или нет."""

        @classmethod
        def safe_init(cls, params: Union[Dict[str, Any], Record]):
            """Безопасная инициализации параметров"""
            return cls(**params)

        def __getattr__(self, item):
            return self.args[item]
