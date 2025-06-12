from broker.broker import Broker
from observation.carcassonne_observation import CarcassonneGameObservation
from concurrent.futures import ThreadPoolExecutor, as_completed


class CarcassonneGameBroker(Broker):
    """
    CarcassonneGameBroker 类继承自 Broker，用于管理卡卡颂游戏中的发布-订阅机制。

    Attributes:
        use_multi_thread (bool): 指示是否使用多线程来通知订阅者。
    """

    def __init__(self, use_multi_thread=False):
        """
        初始化 CarcassonneGameBroker 类的实例。

        Args:
            use_multi_thread (bool): 是否使用多线程来通知订阅者，默认为 False。

        Returns:
            None
        """
        super().__init__()
        self.use_multi_thread = use_multi_thread

    def publish(self, topic, message, image, observation:CarcassonneGameObservation):
        """
        send message到指定的主题，并通知所有订阅该主题的订阅者。

        Args:
            topic (str): send message的主题。
            message (str): 发布的消息内容。
            image (Any): 发布的图像内容。
            observation (CarcassonneGameObservation): 发布的观察内容。

        Returns:
            list: 包含所有订阅者响应的列表。

        Raises:
            None
        """
        if topic in self.subscribers:
            print(f"\033[91msend message [{topic}]: {message}\033[0m")
            responses = []

            def notify_subscriber(subscriber):
                return subscriber.notify(topic, message, image, observation)

            if self.use_multi_thread:
                with ThreadPoolExecutor(max_workers=len(self.subscribers[topic])) as executor:
                    futures = {executor.submit(notify_subscriber, subscriber): subscriber for subscriber in
                               self.subscribers[topic]}

                    for future in as_completed(futures):
                        response = future.result()
                        if response is not None:
                            responses.append(response)
            else:
                for subscriber in self.subscribers[topic]:
                    response = notify_subscriber(subscriber)
                    if response is not None:
                        responses.append(response)

            return responses
        return []
