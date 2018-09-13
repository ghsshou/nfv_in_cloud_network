import random


class Solution:

    def __init__(self, nums):
        """
        :type nums: List[int]
        """
        self.origin = list(nums)
        self.operator = nums

    def reset(self):
        """
        Resets the array to its original configuration and return it.
        :rtype: List[int]
        """
        self.operator = list(self.origin)
        return self.origin

    def shuffle(self):
        """
        Returns a random shuffling of the array.
        :rtype: List[int]
        """
        result = []
        while self.operator:
            print("len", len(self.operator))
            random_index = random.randint(0, len(self.operator) - 1)
            print(random_index)
            result.append(self.operator[random_index])
            self.operator.pop(random_index)
        print(result)
        return result

if __name__ == "__main__":
    sol = Solution([1, 2, 3])
    res = sol.shuffle()
    # print(res)