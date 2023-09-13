from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, List, Union

# internal modules
import exception


@dataclass(frozen=True)
class AsyncInvokeManager:
    """Манагер асинхронных запросов, на основе упорядоченного списка"""
    run_auto: bool = False
    """Запускать задачи сразу после их добавления"""
    __tasks: List[AsyncInvokeManager.Task] = field(init=False,
                                                   default_factory=list)

    @dataclass()
    class Task:
        """Задача, которая полетит в очередь"""
        blo: BLObject
        args: List[Any]
        callback: Callable
        weight: int  # Вес задачи - зависит от тяжести запроса
        #NOTE: хотелось бы, что бы таска сама знала о своем будущем результате
        _future_result: Union[FutureObject, FutureObjectList,
                              FutureObjectVoid] = field(init=False,
                                                        default=None)

        def can_handle(self) -> bool:
            """Может ли происходить обработка результата асинхронного вызова"""
            return self._can_handle()

        def future_call(self):
            """Асинхронный вызов задачи"""
            #TODO: возможность синхронного или асинхронного вызова задач
            self._future_result = self.blo.FutureInvoke(*self.args)

        def handle_result(self) -> Any:
            """Обработать результат вызова"""
            if not self.can_handle():
                # TODO: логирование/вызов future_call/raise
                self.HandleWarning.log_warning(
                    f'Попытка обработки результата вызова перед вызовом. {self}'
                )
            return self._handle_result()

        def _can_handle(self) -> bool:
            """Конкретная реализация флага возможности обработать результат"""
            # можно было сделать проверку на подкласс, оставил так, чтобы можно было расширить на синхронные вызовы
            return self._future_result is not None

        def _handle_result(self) -> Any:
            return self.callback(self._future_result.get())

        class FutureCallWarning(exception.Warning):
            """Исключение при ошибке асинхронного вызова"""

        class HandleWarning(exception.Warning):
            """Исключение при ошибке обработки результата вызова"""

    def add_task(self, blo: BLObject, method_args: List[Any],
                 handler_result: Callable, weight: int):
        """
        Добавить запрос в очередь на исполнение.

        Args:
            blo - экземпляр бизнес-объекта, куда будет уходить запрос
            method_args - первым аргументом является название метода БО, затем его параметры
            handler_result - функция-обработчик результата. Аргументом функции является результат асинхронного вызова
        """
        task = self.Task(blo, method_args, handler_result, weight)
        if self.run_auto:
            task.future_call()
        self.__append(task)

    def __append(self, task: AsynkInvokeManager.Task):
        """Добавить задачу в очередь."""
        if len(self.__tasks) == 0:
            self.__tasks.append(task)
            return
        for i, item in enumerate(self.__tasks):
            if task.weight >= item.weight:
                self.__tasks.insert(i, task)
                return

    @LogNode()
    def start_tasks(self):
        """
        Параллельный запуск запросов и обработка результатов.
        Первыми запускаются задачи с бОльшим весом, обработка результата начинается с задач с меньшим весом.
        """
        if self.run_auto:
            self.ManagerWarning.log_warning(
                f'Попытка запуска задач с run_auto={self.run_auto}')
            return
        for task in self.__tasks:
            task.future_call()

    @LogNode()
    def await_tasks(self):
        """Дождаться выполнения запущенных задач и обработать результат"""
        self.__tasks.reverse()
        for task in self.__tasks:
            task.handle_result()

    class ManagerWarning(exception.Warning):
        """Ворниг"""
