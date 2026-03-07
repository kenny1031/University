'''
Your task is to complete the following functions which are marked by the TODO comment.
You are free to add properties and functions to the class as long as the given signatures remain identical.
Note: Please do not modify any existing function signatures, as it will impact your test results
'''

class Student:
    """Represents a node of a binary tree."""
    """These are the defined properties as described above, feel free to add more if you wish!"""
    """However do not modify nor delete the current properties."""
    def __init__(self, student_id, name, GPA) -> None:
        self.left = None
        self.right = None
        self.parent = None
        self.student_id = student_id
        self.name = name
        self.GPA = GPA
    
    def is_external(self) -> bool:
        if self.left is None and self.right is None:
            return True
        return False

class BSTree:
    """
    Implements an unbalanced Binary Search Tree.
    """
    def __init__(self, *args) -> None:
        self.Root = None

    """-------------------------------PLEASE DO NOT MODIFY THE ABOVE (except you could add more properties in Student class) -------------------------------"""
    def insert(self, student_id, name, GPA) -> None:
        """
        Inserts a new Student into the tree.
        """
        # TODO: Implement the method
        if self.Root is None:
            self.Root = Student(student_id, name, GPA)
            
        else:
            self.insert_recursive(self.Root, student_id, name, GPA)

    def insert_recursive(self, current_node, student_id, name, GPA):

        if student_id < current_node.student_id:
            if current_node.left is None:
                current_node.left = Student(student_id, name, GPA)
            else:
                self.insert_recursive(current_node.left, student_id, name, GPA)
        
        elif student_id > current_node.student_id:
            if current_node.right is None:
                current_node.right = Student(student_id, name, GPA)
            else:
                self.insert_recursive(current_node.right, student_id, name, GPA)
        else:
            pass

    def search(self, student_id) -> Student:
        """
        Searches for a student by student_id.
        """
        # TODO: Implement the method
        return self.search_recursive(self.Root, student_id)
    
    def search_recursive(self, current_node, student_id) -> Student:
        if current_node is None:
            return None
        if student_id == current_node.student_id:
            return current_node
        elif student_id < current_node.student_id:
            return self.search_recursive(current_node.left, student_id)
        else:
            return self.search_recursive(current_node.right, student_id)
        

    def delete(self, student_id) -> None:
        """
        Deletes a student from the tree by student_id.
        """
        # TODO: Implement the method
        self.Root = self.delete_recursive(self.Root, student_id)
    
    def delete_recursive(self, node, student_id) -> Student:
        if node is None:
            return None

        if student_id < node.student_id:
            node.left = self.delete_recursive(node.left, student_id)
        elif student_id > node.student_id:
            node.right = self.delete_recursive(node.right, student_id)
        else:
            # node has no children
            if node.left is None and node.right is None:
                return None
            
            # node has one child
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            
            # node has two children
            r_parent = node.right
            subroot = node.right
            while subroot.left is not None:
                r_parent = subroot
                subroot = subroot.left
            
            node.student_id = subroot.student_id
            node.name = subroot.name
            node.GPA = subroot.GPA

            if subroot == r_parent:
                node.right = subroot.right
            else:
                r_parent.left = subroot.right
        return node
            


    def update_gpa(self, student_id, new_gpa) -> None:
        """
        Updates the GPA of a student.
        """
        # TODO: Implement the method
        student = self.search(student_id)
        if student is not None:
            student.GPA = new_gpa

    def update_name(self, student_id, new_name) -> None:
        """
        Updates the name of a student.
        """
        # TODO: Implement the method
        student = self.search(student_id)
        if student is not None:
            student.name = new_name

    def update_student_id(self, old_id, new_id) -> None:
        """
        Updates the student ID. This requires special handling to maintain tree structure.
        """
        # TODO: Implement the method
        student = self.search(old_id)
        if student is not None:
            self.delete(old_id)
            self.insert(student.student_id, student.name, student.GPA)

    def generate_report(self, student_id) -> str:
        """
        Generates a full report for a student.
        In the format of: Student ID: {student_id}, Name: {student.name}, GPA: {student.GPA}
        Otherwsie, print: No student found with ID {student_id}
        """
        # TODO: Implement the method
        student = self.search(student_id)
        report = f"Student ID: {student.student_id}, Name: {student.name}, GPA: {student.GPA}"
        return report

    def find_max_gpa(self) -> float:
        """
        Finds the maximum GPA in the tree.
        """
        # TODO: Implement the method
        max_gpa = 0
        students = self.inorder()
        for student in students:
            if student.GPA > max_gpa:
                max_gpa = student.GPA
        return max_gpa

    def find_min_gpa(self) -> float:
        """
        Finds the minimum GPA in the tree.
        """
        # TODO: Implement the method
        min_gpa = 100
        students = self.inorder()
        for student in students:
            if student.GPA < min_gpa:
                min_gpa = student.GPA
        return min_gpa

    def levelorder(self, level=None) -> list:
        """
        Performs a level order traversal of the tree. If level is specified, returns all nodes at that level.
        """
        # TODO: Implement the method
        
        ls = []
        queue = []
        queue.append((self.Root, 0))

        while queue != []:
            node, current_level = queue.pop(0)

            if current_level == level or level is None:
                ls.append(node)

            if node.left is not None:
                queue.append((node.left, current_level + 1))

            if node.right != None:
                queue.append((node.right, current_level + 1))

        return ls


    def inorder(self) -> list:
        """
        Performs an in-order traversal of the tree.
        """
        # TODO: Implement the method
        ls = []
        self.inorder_recursive(self.Root, ls)
        return ls

    def inorder_recursive(self, node, ls) -> None:
        
        if node is not None:

            if node.left is not None:
                self.inorder_recursive(node.left, ls)

            ls.append(node)
            if node.right is not None:
                self.inorder_recursive(node.right, ls)


    def is_valid(self) -> bool:
        """
        Checks if the tree is a valid Binary Search Tree. Return True if it is a valid BST, False or raise Exception otherwise.
        """
        # TODO: Implement the method
        return self.validity_help(self.Root)


    def validity_help(self, node) -> bool:

        if node is not None:
            
            if node.left is not None:
                if node.left.student_id > node.student_id:
                    return False
                else:
                    return self.validity_help(node.left)

            if node.right is not None:
                if node.right.student_id < node.student_id:
                    return False
                else:
                    return self.validity_help(node.right)

            return True
