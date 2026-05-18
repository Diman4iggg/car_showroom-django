# Диаграмма моделей CarShowroom

```mermaid
classDiagram
    direction LR

    class User {
        +username: String
        +email: EmailField
        +first_name: String
        +last_name: String
        +is_superuser: Boolean
        +__str__(): String
    }

    class UserProfile {
        +user: User[1]
        +role: String
        +timezone: String
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class Client {
        +user: User[0..1]
        +last_name: String
        +first_name: String
        +middle_name: String
        +birth_date: DateField
        +phone: String
        +email: EmailField
        +city: String
        +address: String
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class Employee {
        +user: User[0..1]
        +last_name: String
        +first_name: String
        +middle_name: String
        +position: String
        +birth_date: DateField
        +phone: String
        +email: EmailField
        +clients: Client[0..*]
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class CarCategory {
        +name: String
        +description: TextField
        +__str__(): String
    }

    class Manufacturer {
        +name: String
        +country: String
        +website: URLField
        +__str__(): String
    }

    class CarFeature {
        +name: String
        +__str__(): String
    }

    class Car {
        +name: String
        +category: CarCategory[1]
        +manufacturer: Manufacturer[1]
        +features: CarFeature[0..*]
        +year: PositiveSmallIntegerField
        +price: DecimalField
        +stock: PositiveIntegerField
        +fuel_type: String
        +color: String
        +description: TextField
        +image: ImageField
        +is_available: Boolean
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class Order {
        +client: Client[1]
        +employee: Employee[0..1]
        +status: String
        +order_date: DateTimeField
        +delivery_date: DateField
        +delivery_at: DateTimeField
        +comment: TextField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +total_amount: DecimalField
        +__str__(): String
    }

    class OrderItem {
        +order: Order[1]
        +car: Car[1]
        +quantity: PositiveIntegerField
        +unit_price: DecimalField
        +total_price: DecimalField
        +__str__(): String
    }

    class Sale {
        +order: Order[1]
        +paid_at: DateTimeField
        +total_amount: DecimalField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class CompanyInfo {
        +title: String
        +text: TextField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class NewsArticle {
        +title: String
        +summary: String
        +body: TextField
        +image: ImageField
        +is_published: Boolean
        +published_at: DateTimeField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class FAQ {
        +question: String
        +answer: TextField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class ContactEmployee {
        +full_name: String
        +position: String
        +work_description: TextField
        +phone: String
        +email: EmailField
        +photo: ImageField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class Vacancy {
        +title: String
        +description: TextField
        +is_active: Boolean
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class PrivacyPolicy {
        +title: String
        +text: TextField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class Review {
        +author_name: String
        +rating: PositiveSmallIntegerField
        +text: TextField
        +is_published: Boolean
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    class PromoCode {
        +code: String
        +description: TextField
        +discount_percent: PositiveSmallIntegerField
        +starts_at: DateField
        +ends_at: DateField
        +is_active: Boolean
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__(): String
    }

    User "1" -- "1" UserProfile : OneToOne
    User "0..1" -- "0..1" Client : OneToOne
    User "0..1" -- "0..1" Employee : OneToOne
    Employee "0..*" -- "0..*" Client : ManyToMany

    Manufacturer "1" -- "0..*" Car : ForeignKey
    CarCategory "1" -- "0..*" Car : ForeignKey
    Car "0..*" -- "0..*" CarFeature : ManyToMany

    Client "1" -- "0..*" Order : ForeignKey
    Employee "0..1" -- "0..*" Order : ForeignKey
    Order "1" -- "1..*" OrderItem : ForeignKey
    Car "1" -- "0..*" OrderItem : ForeignKey
    Order "1" -- "0..1" Sale : OneToOne
```

## Основные связи

- `User` и `UserProfile` связаны через `OneToOneField`.
- `Client` и `Employee` могут быть связаны с `User` через `OneToOneField`.
- `Employee` и `Client` связаны через `ManyToManyField`.
- `Car` связан с `Manufacturer` и `CarCategory` через `ForeignKey`.
- `Car` и `CarFeature` связаны через `ManyToManyField`.
- `Order` связан с `Client` и `Employee` через `ForeignKey`.
- `OrderItem` связывает `Order` и `Car`.
- `Sale` связан с `Order` через `OneToOneField`.
