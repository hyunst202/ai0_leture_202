class KDTStudent:
    def __init__(self, name: str, track: str):
        self.name = name
        self.track = track
        self.level = 1
        self.energy = 100
        self.completed_missions = []
    def study_coding(self, topic: str, cost_energy: int = 25) -> str:
        if self.energy < cost_energy:
            return f"[휴식 필요] {self.name}님의 에너지가 부족합니다! (현재: {self.energy})"
        self.energy -= cost_energy
        self.level += 1
        self.completed_missions.append(topic)
        return f"[레벨업!] {self.name}님이 '{topic}' 실습을 완료했습니다! (Lv.{self.level}, 남은 에너지: {self.energy})"
    def drink_coffee(self, boost: int = 40) -> str:
        self.energy = min(100, self.energy + boost)
        return f"[충전 완료] 아이스 아메리카노 수혈! 현재 에너지: {self.energy}"
student1 = KDTStudent("김루키", "AI 엔지니어링")
print(student1.study_coding("Python 클래스기초"))
print(student1.study_coding("예외처리 마스터"))
print(student1.drink_coffee())

